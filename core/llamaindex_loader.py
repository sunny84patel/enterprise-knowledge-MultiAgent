"""
core/llamaindex_loader.py — LlamaIndex PageIndex Query Engine  (NEW — resume differentiator)
Exposes a query interface over the LlamaIndex-ingested collection.
Used as a secondary retrieval path for page-level semantic queries.
"""

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.query_engine import RetrieverQueryEngine

from db.qdrant import get_qdrant_client
from config import settings


class LlamaIndexPageRetriever:
    def __init__(self):
        client = get_qdrant_client()
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=f"{settings.QDRANT_COLLECTION}_llama",
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
        )
        self.retriever = index.as_retriever(similarity_top_k=3)

    async def retrieve(self, query: str):
        """Return LlamaIndex NodeWithScore objects."""
        nodes = await self.retriever.aretrieve(query)
        return nodes
