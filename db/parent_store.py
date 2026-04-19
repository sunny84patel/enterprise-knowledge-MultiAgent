"""
db/parent_store.py — Parent Chunk Store
Maps child chunk IDs back to their parent chunks.
Enables parent-document retrieval: search on child, return parent context.
"""

from typing import Dict, Optional
import json
import os

STORE_PATH = "data/parent_store.json"


class ParentChunkStore:
    """Simple JSON-backed store for parent-child chunk mapping."""

    def __init__(self, path: str = STORE_PATH):
        self.path = path
        self._store: Dict[str, str] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self._store = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._store, f, indent=2)

    def save_parent(self, child_id: str, parent_content: str):
        self._store[child_id] = parent_content
        self._save()

    def get_parent(self, child_id: str) -> Optional[str]:
        return self._store.get(child_id)

    def clear(self):
        self._store = {}
        self._save()
