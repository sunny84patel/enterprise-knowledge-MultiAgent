"""
core/compressor.py — LLM-based Context Compressor  (from Repo 1)
Removes irrelevant sentences from retrieved docs before synthesis.
Reduces hallucination and stays within context window limits.
"""

from typing import List
from langchain_core.documents import Document
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever

from core.llm_factory import get_llm


class ContextCompressor:
    def __init__(self):
        self.llm = get_llm()
        self.compressor = LLMChainExtractor.from_llm(self.llm)

    async def compress(self, query: str, docs: List[Document]) -> List[Document]:
        """Extract only relevant sentences from each document."""
        compressed = []
        for doc in docs:
            try:
                result = self.compressor.compress_documents([doc], query)
                if result:
                    compressed.extend(result)
                else:
                    compressed.append(doc)   # keep original if compression returns empty
            except Exception:
                compressed.append(doc)
        return compressed
