# C1 Enterprise AI — Unified Multi-Hop Business Intelligence Layer

An enterprise-grade, agentic RAG prototype designed to unify fragmented, cross-departmental business data (SAP, Salesforce, Dynamics, PDF logs, and internal emails) into a conversational intelligence engine.

---

## 🏗 Architecture Overview

[ Synthetic Data ] -> [ Ingestion & Metadata Chunking ] -> [ ChromaDB Vector Store ]
|
[ Streamlit UI ] <-> [ FastAPI App (Basic Auth) ] <-> [ LangGraph Multi-Hop Agent ]
|
[ Structured Citations Output ]


The system operates on an iterative **LangGraph reasoning loop**:
1. **Query Planning:** Breaks down multi-hop questions into departmental sub-queries.
2. **Metadata-Filtered Retrieval:** Queries vector store with department and source filters.
3. **Re-Evaluation & Cross-Checking:** Detects missing fields, policy overrides, and pricing conflicts.
4. **Evidence Synthesis:** Generates answer with exact document citations and explicit risk flags.

---

## 🛠 Tech Stack Choices & Justifications

* **Language & Framework:** Python 3.12, FastAPI (Fast async execution, auto OpenAPI generation).
* **Orchestration:** LangGraph (Provides deterministic graph state management over raw chain pipelines).
* **Vector Store:** ChromaDB (Zero-dependency local persistence for rapid prototyping).
* **LLM Engine:** OpenAI `gpt-4o-mini` (High tool-calling precision and reliable structured outputs).
* **Frontend:** Streamlit (Instant interactive browser testing for evaluators).

---

## 🚀 Quickstart & Setup

### Option A: Docker Compose (Recommended)
```bash
# 1. Clone repo and set API key
cp .env.example .env
# Edit .env and set your GROQ_API_KEY

# 2. Build and launch services
docker-compose up --build

    API Documentation: http://localhost:8000/docs

    Streamlit Browser Interface: http://localhost:8501

Option B: Local Python Run
Bash

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Seed data and run tests
python generate_synthetic_data.py

# Run API and UI
uvicorn main:app --reload --port 8000
streamlit run app_ui.py