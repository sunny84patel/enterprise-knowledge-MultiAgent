"""
db/qdrant.py — Qdrant Vector Store Client
Singleton client for all Qdrant interactions.
Handles collection creation if it doesn't exist.
"""

from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, HnswConfigDiff,
    SparseVectorParams, SparseIndexParams,
)
from config import settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )
    _ensure_collections(client)
    return client


def _ensure_collections(client: QdrantClient):
    """Create collections if they don't exist yet."""

    # --- Main LangChain child-chunk collection (dense + sparse hybrid) ---
    existing = [c.name for c in client.get_collections().collections]

    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config={
                "dense": VectorParams(
                    size=settings.EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            },
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
        )
        print(f"✅ Created Qdrant collection: {settings.QDRANT_COLLECTION}")

    # --- LlamaIndex PageIndex collection (dense only) ---
    llama_collection = f"{settings.QDRANT_COLLECTION}_llama"
    if llama_collection not in existing:
        client.create_collection(
            collection_name=llama_collection,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
        print(f"✅ Created Qdrant collection: {llama_collection}")
