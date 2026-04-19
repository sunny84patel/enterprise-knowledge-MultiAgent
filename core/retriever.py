"""
core/retriever.py — Hybrid Dense + BM25 Retriever  (from Repo 1)
Combines:
  - Dense vector search (Qdrant cosine similarity)
  - Sparse BM25 keyword search
  - Reciprocal Rank Fusion (RRF) for final ranking
"""

from typing import List
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore, RetrievalMode

from db.qdrant import get_qdrant_client
from core.llm_factory import get_embeddings
from config import settings


class HybridRetriever:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.client = get_qdrant_client()

    def _get_store(self) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=self.client,
            collection_name=settings.QDRANT_COLLECTION,
            embedding=self.embeddings,
            retrieval_mode=RetrievalMode.DENSE,  # dense only (ingestion uses dense; HYBRID needs sparse_embedding)
            vector_name="dense",
        )

    async def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """Run hybrid retrieval and return ranked documents."""
        store = self._get_store()
        retriever = store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k},
        )
        docs = await retriever.ainvoke(query)
        return docs

    async def retrieve_with_scores(self, query: str, top_k: int = 5):
        """Returns (doc, score) tuples for evaluation purposes."""
        store = self._get_store()
        return await store.asimilarity_search_with_score(query, k=top_k)
