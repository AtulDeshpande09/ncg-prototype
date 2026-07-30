import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent

# Initialize persistent ChromaDB vector store locally
CHROMA_PATH = str(SCRIPT_DIR.parent / "chroma_db")
COLLECTION_NAME = "novacart"

client = chromadb.PersistentClient(path=CHROMA_PATH)


DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "synthetic_docs"

embed_key=os.environ.get("VOYAGE_API_KEY")
if not embed_key:
    raise ValueError("VOYAGE_API_KEY environment variable is missing!")

voyage_ef = embedding_functions.VoyageAIEmbeddingFunction(
    api_key=embed_key, 
    model_name="voyage-4-lite"
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=voyage_ef,
    metadata={"hnsw:space": "cosine"}
)


def load_and_parse_files(data_dir: Path = DEFAULT_DATA_DIR) -> List[Dict[str, Any]]:
    """Loads CSV, JSON, MD, and TXT files and converts them into structured document chunks."""
    documents = []

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        ext = os.path.splitext(filename)[1].lower()

        # Parse JSON (Support Tickets)
        if ext == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                text_content = f"Support Ticket ID: {data.get('ticket_id')}\n" \
                               f"Order ID: {data.get('order_id')}\n" \
                               f"Subject: {data.get('subject')}\n" \
                               f"Description: {data.get('description')}\n" \
                               f"Resolution: {data.get('resolution', '')}\n" \
                               f"Flagged Component: {data.get('flagged_component', '')}"
                
                documents.append({
                    "id": data.get("ticket_id", filename),
                    "content": text_content,
                    "metadata": {
                        "department": data.get("department", "Customer Support"),
                        "source_type": "json_ticket",
                        "filename": filename
                    }
                })

        # Parse CSV (Orders, Refunds, Shipments)
        elif ext == ".csv":
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # Deduce department and content based on CSV type
                dept = "Finance" if "refund" in filename else "Sales"
                if "shipment" in filename:
                    dept = "Logistics"

                for idx, row in enumerate(rows):
                    row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                    doc_id = f"{filename}_{idx}"
                    
                    documents.append({
                        "id": doc_id,
                        "content": f"Record from {filename}:\n{row_str}",
                        "metadata": {
                            "department": row.get("department", dept),
                            "source_type": "csv_record",
                            "filename": filename
                        }
                    })

        # Parse Markdown & TXT (Policies, QC Reports, Internal Emails)
        elif ext in [".md", ".txt"]:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Basic metadata extraction rules
                dept = "General"
                if "Department:" in content:
                    try:
                        dept = content.split("Department:")[1].split("\n")[0].strip()
                    except IndexError:
                        pass
                elif "policy" in filename:
                    dept = "Operations"
                elif "marketing" in filename:
                    dept = "Marketing"

                documents.append({
                    "id": filename,
                    "content": content,
                    "metadata": {
                        "department": dept,
                        "source_type": "text_document",
                        "filename": filename
                    }
                })

    return documents


def index_documents():
    """Indexes processed documents into the ChromaDB vector store."""
    docs = load_and_parse_files()
    
    ids = [d["id"] for d in docs]
    contents = [d["content"] for d in docs]
    metadatas = [d["metadata"] for d in docs]

    print(f"Indexing {len(docs)} document chunks into ChromaDB...")
    
    # Upsert documents into vector database
    collection.upsert(
        ids=ids,
        documents=contents,
        metadatas=metadatas
    )
    print("Indexing complete!")

def search_knowledge_base(query: str, department_filter: Optional[str] = None, top_k: int = 4) -> List[Dict[str, Any]]:
    """Performs semantic search with optional metadata filtering."""
    where_clause = {}
    if department_filter:
        where_clause["department"] = department_filter

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_clause if where_clause else None
    )

    formatted_results = []
    if results and results["documents"]:
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "document_id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })

    return formatted_results

if __name__ == "__main__":
    index_documents()
    
    # Quick Test: Metadata Filtered Query
    print("\n--- Testing Search with Department Filter ('Customer Support') ---")
    test_res = search_knowledge_base("overheating laptop power supply", department_filter="Customer Support")
    for r in test_res:
        print(f"ID: {r['document_id']} | Dept: {r['metadata']['department']}")
        print(f"Snippet: {r['content'][:120]}...\n")