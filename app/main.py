import os
import secrets
import shutil
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import local modules
from ingestion import collection, index_documents, load_and_parse_files
from agent import run_multi_hop_query, StructuredAgentResponse, Citation

# ==========================================
# 1. APPLICATION SETUP & SECURITY
# ==========================================

app = FastAPI(
    title="NovaCart AI Enterprise Intelligence Engine",
    description="Unified AI reasoning layer across disconnected enterprise data sources.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# Hardcoded Basic Auth credentials for assessment scope (Section 6.1 requirement)
ADMIN_USERNAME = os.getenv("API_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("API_ADMIN_PASSWORD", "nova1234")

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Validates HTTP Basic Auth credentials against hardcoded/seeded values."""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ==========================================
# 2. SCHEMAS
# ==========================================

class QueryRequest(BaseModel):
    question: str = Field(
        ..., 
        example="Why did Apex Pro Laptop refunds increase in March 2026, and which supplier was responsible?"
    )
    department_filter: Optional[str] = Field(
        None, 
        example="Customer Support",
        description="Optional filter to restrict search scope to a single department."
    )

class HealthCheckResponse(BaseModel):
    status: str
    vector_store_documents_count: int
    api_version: str

class UploadResponse(BaseModel):
    filename: str
    message: str
    total_indexed_documents: int

# ==========================================
# 3. ENDPOINTS
# ==========================================

@app.get("/api/v1/health", response_model=HealthCheckResponse, tags=["System"])
def health_check():
    """
    Public health check endpoint that verifies system status and vector store connectivity.
    """
    try:
        doc_count = collection.count()
        return HealthCheckResponse(
            status="healthy",
            vector_store_documents_count=doc_count,
            api_version="1.0.0"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System unhealthy: {str(e)}")

@app.post("/api/v1/query", response_model=StructuredAgentResponse, tags=["Reasoning Engine"])
def query_business_intelligence(
    request: QueryRequest,
    username: str = Depends(authenticate_user)
):
    """
    Protected endpoint to ask multi-hop business questions across disconnected enterprise sources.
    Returns structured evidence, citations, and inconsistency flags.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
        
    try:
        response = run_multi_hop_query(
            query=request.question,
            department_filter=request.department_filter
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred during multi-hop reasoning: {str(e)}"
        )

@app.post("/api/v1/documents/upload", response_model=UploadResponse, tags=["Data Management"])
async def upload_document(
    file: UploadFile = File(...),
    username: str = Depends(authenticate_user)
):
    """
    Protected endpoint to upload new enterprise documents (CSV, JSON, MD, TXT) and dynamically re-index them into ChromaDB.
    """
    data_dir = "./data/synthetic_docs"
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Re-index all documents to include newly added document
        index_documents()
        updated_count = collection.count()
        
        return UploadResponse(
            filename=file.filename,
            message="File uploaded and vector store successfully updated.",
            total_indexed_documents=updated_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file upload: {str(e)}")

# ==========================================
# 4. STARTUP EVENTS
# ==========================================

@app.on_event("startup")
def startup_event():
    """Initializes the vector database on API startup if unindexed."""
    if collection.count() == 0:
        print("Vector database empty on startup. Triggering ingestion pipeline...")
        index_documents()
    else:
        print(f"Vector store ready with {collection.count()} chunks indexed.")