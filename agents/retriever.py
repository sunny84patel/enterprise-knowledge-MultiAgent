"""
agents/retriever.py — Retriever Agent  (from Repo 1)
Performs hybrid dense + BM25 retrieval from Qdrant,
then applies LLM-based context compression.
"""

from langchain_core.documents import Document
from typing import List

from core.retriever import HybridRetriever
from core.compressor import ContextCompressor
from config import settings


class RetrieverAgent:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.compressor = ContextCompressor()

    async def run(self, query: str) -> List[Document]:
        # Step 1: Hybrid retrieval (dense + BM25)
        docs = await self.retriever.retrieve(query, top_k=settings.TOP_K_RETRIEVAL)

        # Step 2: Context compression — keep only relevant sentences
        if docs:
            docs = await self.compressor.compress(query, docs)

        return docs
