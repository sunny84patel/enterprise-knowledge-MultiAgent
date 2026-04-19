from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import traceback
import os

from agents.graph import build_graph
from core.indexer import ingest_document
from observability.tracer import init_langsmith
from config import settings

app = FastAPI(
    title="Enterprise Knowledge Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://enterprise-knowledge-multi-agent.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ❌ DO NOT build graph globally
agent_graph = None


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    stream: Optional[bool] = False


@app.on_event("startup")
async def startup_event():
    global agent_graph

    print("🚀 Starting app...")
    print("PORT:", os.getenv("PORT"))

    try:
        init_langsmith()
        print("✅ LangSmith initialized")

        # ⚠️ Build graph safely (can fail without crashing server)
        agent_graph = build_graph()
        print("✅ Agent graph ready")

    except Exception as e:
        print("❌ Startup error:", str(e))
        agent_graph = None


@app.get("/")
async def root():
    return {"status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.LLM_MODEL}


@app.post("/chat")
async def chat(request: QueryRequest):
    if agent_graph is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

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
    try:
        content = await file.read()
        doc_count = await ingest_document(content, file.filename or "document")
        return {"message": f"Ingested {doc_count} chunks"}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))