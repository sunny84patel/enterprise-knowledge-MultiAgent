"""
Central config — reads from .env
All model choices, API keys, and vector DB settings live here.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # --- LLM ---
    LLM_PROVIDER: str = "groq"           # "groq" | "openai" | "ollama"
    LLM_MODEL: str = "llama-3.1-8b-instant"  # groq (llama3-8b-8192 decommissioned) | openai: gpt-4o | ollama: llama3
    LLM_TEMPERATURE: float = 0.0
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # --- Qdrant ---
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "knowledge_base"

    # --- LlamaIndex ---
    LLAMA_CHUNK_SIZE: int = 512
    LLAMA_CHUNK_OVERLAP: int = 50

    # --- LangSmith Observability ---
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "enterprise-knowledge-agent"

    # --- Web Search Fallback ---
    TAVILY_API_KEY: Optional[str] = None

    # --- RAG ---
    TOP_K_RETRIEVAL: int = 5
    MAX_CONTEXT_LENGTH: int = 4000
    REWRITE_MAX_ATTEMPTS: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
