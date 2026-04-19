"""
Enterprise Knowledge Agent — Main FastAPI Entry Point
Combined: agentic-rag-for-dummies (Repo 1) + Multi-Agentic-RAG (Repo 2)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import traceback
import uvicorn

from agents.graph import build_graph
from core.indexer import ingest_document
from observability.tracer import init_langsmith
from config import settings

app = FastAPI(
    title="Enterprise Knowledge Agent",
    description="Multi-Agent RAG with LangGraph + LlamaIndex + Qdrant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build the LangGraph agent graph once at startup
agent_graph = build_graph()


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    stream: Optional[bool] = False


@app.on_event("startup")
async def startup_event():
    init_langsmith()
    print("✅ LangSmith tracing initialized")
    print("✅ Agent graph compiled")
    print(f"✅ Using model: {settings.LLM_MODEL}")


@app.post("/chat")
async def chat(request: QueryRequest):
    """Main chat endpoint — runs query through the full agent pipeline."""
    try:
        result = await agent_graph.ainvoke({
            "query": request.query,
            "session_id": request.session_id,
            "messages": [],
            "retrieved_docs": [],
            "rewritten_query": None,
            "fact_check_passed": None,
            "final_answer": None,
            "agent_trace": [],
        })
        return {
            "answer": result["final_answer"],
            "agent_trace": result["agent_trace"],
            "sources": [doc.metadata for doc in result.get("retrieved_docs", [])],
            "session_id": request.session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """Upload and index a PDF or text document into Qdrant."""
    try:
        content = await file.read()
        doc_count = await ingest_document(content, file.filename or "document")
        return {"message": f"Ingested {doc_count} chunks from '{file.filename}'"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.LLM_MODEL}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[".venv", ".git", "__pycache__", "*.pyc"],
    )
