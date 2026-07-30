import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

# Config & Page Setup
st.set_page_config(
    page_title="C1 AI - Unified Intelligence Layer",
    page_icon="🤖",
    layout="wide"
)

# Sidebar - Configuration & Authentication
st.sidebar.title(" API Credentials & Settings")
api_url = st.sidebar.text_input("FastAPI Base URL", value="http://localhost:8000")
username = st.sidebar.text_input("Username", value="admin")
password = st.sidebar.text_input("Password", value="c1secret2026", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader(" System Status")

# System Health Check Button
if st.sidebar.button("Check Backend Health"):
    try:
        res = requests.get(f"{api_url}/api/v1/health", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.sidebar.success(f"Status: {data['status'].upper()}")
            st.sidebar.info(f"Indexed Documents: {data['vector_store_documents_count']}")
        else:
            st.sidebar.error(f"Error: {res.status_code}")
    except Exception as e:
        st.sidebar.error(f"Cannot connect to backend: {str(e)}")

# Main Interface
st.title("Novacart Enterprise AI Reasoning Portal")
st.caption("Ask natural-language questions across disconnected enterprise data sources (SAP, Salesforce, Dynamics, etc.)")

st.markdown("---")

# Quick Preset Multi-Hop Questions for Evaluators
st.subheader(" Evaluator Quick-Test Presets")
preset_questions = [
    "Select a pre-configured multi-hop test query...",
    "Why did Apex Pro Laptop refunds increase in March 2026, and which supplier was responsible?",
    "Is a customer eligible for a full refund on an Apex Pro Laptop purchased 35 days ago?",
    "What warehouse supply chain bottleneck occurred in March 2026 due to QC audits?"
]

selected_preset = st.selectbox("Choose a sample business query:", preset_questions)

# Query Input Form
with st.form("query_form"):
    default_text = "" if selected_preset.startswith("Select") else selected_preset
    user_query = st.text_area("Your Business Question:", value=default_text, height=100)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        dept_filter = st.selectbox(
            "Department Filter (Optional):",
            [None, "Customer Support", "Sales", "Finance", "Logistics", "Operations", "Marketing"]
        )
    
    submit_button = st.form_submit_button("Run Multi-Hop Analysis", type="primary")

# Execute Query
if submit_button and user_query.strip():
    with st.spinner("Executing multi-hop agentic reasoning loop across enterprise systems..."):
        try:
            payload = {
                "question": user_query,
                "department_filter": dept_filter if dept_filter else None
            }
            
            response = requests.post(
                f"{api_url}/api/v1/query",
                json=payload,
                auth=HTTPBasicAuth(username, password),
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.markdown("---")
                
                # Confidence Meter & Header
                conf = result.get("confidence_score", 0.0)
                metric_col, _ = st.columns([1, 3])
                with metric_col:
                    st.metric("Reasoning Confidence", f"{int(conf * 100)}%")
                
                # Answer Block
                st.subheader("📝 Answer & Executive Summary")
                st.markdown(result["answer"])
                
                st.markdown("---")
                
                # Citations & Evidence Section
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("📌 Evidence & Citations")
                    citations = result.get("citations", [])
                    if citations:
                        for idx, c in enumerate(citations, 1):
                            with st.expander(f"Citation {idx}: {c['document_id']} ({c['source_type']})"):
                                st.write(f"**Snippet:** _{c['relevant_snippet']}_")
                    else:
                        st.info("No direct document citations attached.")

                # Inconsistency / Uncertainty Flags Section
                with col_right:
                    st.subheader("⚠️ Detected Inconsistencies & Flags")
                    flags = result.get("uncertainties_and_inconsistencies", [])
                    if flags:
                        for flag in flags:
                            st.warning(f"**Flagged:** {flag}")
                    else:
                        st.success("No policy conflicts, missing fields, or discrepancies detected.")

            elif response.status_code == 401:
                st.error("Authentication failed! Check API credentials in sidebar.")
            else:
                st.error(f"Backend Error [{response.status_code}]: {response.text}")
                
        except Exception as e:
            st.error(f"Failed to communicate with FastAPI server: {str(e)}")

# File Upload Tool in Sidebar/Expander
with st.expander("📁 Upload New Document to Vector Database"):
    uploaded_file = st.file_uploader("Upload CSV, JSON, Markdown, or TXT file", type=["csv", "json", "md", "txt"])
    if st.button("Index File") and uploaded_file:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        res = requests.post(
            f"{api_url}/api/v1/documents/upload",
            files=files,
            auth=HTTPBasicAuth(username, password)
        )
        if res.status_code == 200:
            st.success("File uploaded and vector store updated!")
        else:
            st.error(f"Upload failed: {res.text}")