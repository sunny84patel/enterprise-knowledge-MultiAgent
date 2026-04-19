"""
core/indexer.py — Document Ingestion Pipeline  (Repo 1 + LlamaIndex NEW)
Dual ingestion:
  1. LlamaIndex PageIndex    → semantic page-level chunks
  2. LangChain parent-child  → fine-grained sentence-level chunks
Both stored in Qdrant for hybrid retrieval.
"""

import tempfile
import os
from typing import Optional

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.qdrant import QdrantVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from db.qdrant import get_qdrant_client
from core.llm_factory import get_embeddings
from config import settings

# Use same HuggingFace embeddings for LlamaIndex (avoids OpenAI default; avoids safe_serialization issue)
def _set_llama_embed_model():
    from llama_index.core import Settings
    Settings.embed_model = get_embeddings()


async def ingest_document(content: bytes, filename: str) -> int:
    """
    Ingest a PDF or text file into Qdrant.
    Returns number of chunks stored.
    """
    suffix = ".pdf" if filename.endswith(".pdf") else ".txt"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    errors = []
    chunk_count = 0

    try:
        # --- Path 1: LlamaIndex PageIndex (semantic chunking) ---
        try:
            chunk_count += await _ingest_with_llamaindex(tmp_path, filename or "document")
        except Exception as e:
            errors.append(f"LlamaIndex: {e!s}")

        # --- Path 2: LangChain fine-grained parent-child chunks ---
        try:
            chunk_count += await _ingest_with_langchain(tmp_path, filename or "document")
        except Exception as e:
            errors.append(f"LangChain: {e!s}")

        if errors:
            raise RuntimeError("; ".join(errors))
        return chunk_count
    finally:
        os.unlink(tmp_path)


async def _ingest_with_llamaindex(filepath: str, source_name: str) -> int:
    """LlamaIndex PageIndex ingestion — good for page-level semantic search."""
    _set_llama_embed_model()
    client = get_qdrant_client()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=f"{settings.QDRANT_COLLECTION}_llama",
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    reader = SimpleDirectoryReader(input_files=[filepath])
    documents = reader.load_data()

    parser = SentenceSplitter(
        chunk_size=settings.LLAMA_CHUNK_SIZE,
        chunk_overlap=settings.LLAMA_CHUNK_OVERLAP,
    )

    # Attach source metadata
    for doc in documents:
        doc.metadata["source"] = source_name
        doc.metadata["ingestion_method"] = "llamaindex"

    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        transformations=[parser],
    )
    return len(documents)


async def _ingest_with_langchain(filepath: str, source_name: str) -> int:
    """LangChain parent-child chunking — fine-grained retrieval."""
    from langchain_qdrant import QdrantVectorStore as LCQdrant

    # Load document
    if filepath.endswith(".pdf"):
        loader = PyPDFLoader(filepath)
    else:
        loader = TextLoader(filepath)
    docs = loader.load()

    # Parent chunks (larger context)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    # Child chunks (precise retrieval)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)

    parent_chunks = parent_splitter.split_documents(docs)
    child_chunks = child_splitter.split_documents(docs)

    for chunk in child_chunks:
        chunk.metadata["source"] = source_name
        chunk.metadata["ingestion_method"] = "langchain_child"

    embeddings = get_embeddings()
    client = get_qdrant_client()

    LCQdrant.from_documents(
        child_chunks,
        embedding=embeddings,
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION,
        api_key=settings.QDRANT_API_KEY,
        vector_name="dense",
    )

    return len(child_chunks)
