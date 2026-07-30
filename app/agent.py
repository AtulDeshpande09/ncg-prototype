import json
from typing import List, Optional, Annotated, TypedDict
from pydantic import BaseModel, Field

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Import search function from ingestion module
from ingestion import search_knowledge_base

# ==========================================
# 1. STRUCTURED OUTPUT & SCHEMAS
# ==========================================

class Citation(BaseModel):
    document_id: str = Field(description="The unique document ID or filename cited.")
    source_type: str = Field(description="The document type (e.g. csv_record, json_ticket, text_document).")
    relevant_snippet: str = Field(description="A brief excerpt or sentence supporting the claim.")

class StructuredAgentResponse(BaseModel):
    answer: str = Field(
        description="Comprehensive, step-by-step synthesized answer to the user's business question."
    )
    citations: List[Citation] = Field(
        default=[],
        description="Explicit list of supporting evidence sources used to generate the answer."
    )
    uncertainties_and_inconsistencies: List[str] = Field(
        default=[],
        description="Explicit flags for missing fields, conflicting policies, or discrepancies encountered."
    )
    confidence_score: float = Field(
        description="Confidence score between 0.0 and 1.0 based on evidence completeness."
    )

# ==========================================
# 2. RETRIEVAL TOOLS
# ==========================================

@tool
def query_knowledge_base(query: str, department_filter: Optional[str] = None) -> str:
    """
    Searches the Novacart Enterprise Knowledge Base for relevant documents, orders, tickets, or reports.
    Supports optional department filtering ('Sales', 'Finance', 'Customer Support', 'Logistics', 'Operations', 'Marketing').
    """
    results = search_knowledge_base(query=query, department_filter=department_filter, top_k=2)
    if not results:
        return "No relevant records found in the knowledge base for this query."
    
    formatted_docs = []
    for doc in results:
        formatted_docs.append(
            f"--- Document ID: {doc['document_id']} (Type: {doc['metadata']['source_type']}, Dept: {doc['metadata']['department']}) ---\n"
            f"{doc['content']}\n"
        )
    return "\n".join(formatted_docs)

tools = [query_knowledge_base]
tools_by_name = {t.name: t for t in tools}

# ==========================================
# 3. LANGGRAPH STATE & AGENT DEFINITION
# ==========================================

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    department_filter: Optional[str]

LLM = ChatGroq(
    model="openai/gpt-oss-120b", 
    temperature=0.1
)

COMPRESSOR_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0
)


LLM_WITH_TOOLS = LLM.bind_tools(tools)

SYSTEM_PROMPT = """You are NovaCart AI, an enterprise business intelligence agent capable of multi-hop reasoning across disconnected company systems (SAP, Salesforce, Dynamics, etc.).

YOUR REASONING PROCESS:
1. Break complex business questions into sub-queries.
2. Execute searches using the `query_knowledge_base` tool to gather evidence from multiple departments (e.g., check orders -> check support tickets -> check supplier logs).
3. Always verify if policies have active overrides, if records conflict (e.g., price vs store credit), or if data fields are missing.
4. Continue searching until you have complete multi-hop evidence or have exhausted available sources.

CRITICAL INSTRUCTIONS:
- You must ground every claim in retrieved evidence.
- Actively flag any conflicting records, outdated policies, or missing data in your final analysis.
"""

def call_model(state: AgentState):
    """Executes the LLM with system prompt and current message state."""

    current_messages = state["messages"]

    if len(current_messages) > 5:
        optimized_history = [current_messages[0]] + current_messages[-4:]
    else:
        optimized_history = current_messages

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + optimized_history
    response = LLM_WITH_TOOLS.invoke(messages)
    return {"messages": [response]}



def execute_tools(state: AgentState):
    """Executes tool calls and compresses text outputs to respect TPM limits."""
    last_message = state["messages"][-1]
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_func = tools_by_name[tool_call["name"]]
        args = tool_call["args"]
        if state.get("department_filter") and "department_filter" not in args:
            args["department_filter"] = state["department_filter"]
            
        raw_output = str(tool_func.invoke(args))
        
        # Tool Compression: If tool output is bulky, use a cheaper model to strip noise
        if len(raw_output) > 1500:
            compression_prompt = (
                f"Extract only key matching metrics, statuses, names, or timelines "
                f"relevant to the query. Summarize into a concise, factual note under 250 words:\n\n{raw_output}"
            )
            try:
                compressed_output = COMPRESSOR_LLM.invoke(compression_prompt).content
                final_output = f"[Compressed Content]: {compressed_output}"
            except Exception:
                final_output = raw_output[:1500] + "\n...[Truncated due to token length limit]..."
        else:
            final_output = raw_output

        tool_messages.append(
            ToolMessage(
                content=final_output,
                tool_call_id=tool_call["id"],
                name=tool_call["name"]
            )
        )
    return {"messages": tool_messages}



def should_continue(state: AgentState) -> str:
    """Determines whether to execute tools or end the reasoning loop."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# Construct the Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", execute_tools)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

graph_agent = workflow.compile()

# ==========================================
# 4. ENTRYPOINT FUNCTION
# ==========================================

def run_multi_hop_query(query: str, department_filter: Optional[str] = None) -> StructuredAgentResponse:
    """
    Executes the multi-hop reasoning graph and formats the final answer into a structured response.
    """
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "department_filter": department_filter
    }
    
    # Run graph execution
    final_state = graph_agent.invoke(initial_state)
    conversation_history = final_state["messages"]
    
    # Force structured evaluation of gathered evidence
    structured_llm = LLM.with_structured_output(StructuredAgentResponse)
    
    formatting_prompt = f"""Review the following reasoning history and generate a structured enterprise summary with explicit citations and inconsistency flags.

Question: {query}

Full Conversation & Evidence Retrieved:
{[msg.content for msg in conversation_history]}
"""
    
    structured_response = structured_llm.invoke(formatting_prompt)
    return structured_response

# ==========================================
# 5. LOCAL EXECUTION TEST
# ==========================================

if __name__ == "__main__":
    import os
    if "GROQ_API_KEY" not in os.environ:
        print("Please set your GROQ_API_KEY environment variable to test locally.")
        exit()

    print("\n=======================================================")
    print("TESTING MULTI-HOP REASONING QUERY")
    print("=======================================================\n")
    
    test_query = "Why did Apex Pro Laptop refunds increase in March 2026, and which supplier and component were responsible?"
    
    print(f"User Query: '{test_query}'\n")
    result = run_multi_hop_query(test_query)
    
    print(f"--- ANSWER ---\n{result.answer}\n")
    print(f"--- CONFIDENCE SCORE: {result.confidence_score} ---\n")
    
    print("--- CITATIONS ---")
    for c in result.citations:
        print(f"• [{c.document_id}] ({c.source_type}): {c.relevant_snippet}")
        
    print("\n--- UNCERTAINTIES & INCONSISTENCIES FLAGGED ---")
    for flag in result.uncertainties_and_inconsistencies:
        print(f"⚠️ {flag}")