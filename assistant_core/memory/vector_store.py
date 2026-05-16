from __future__ import annotations

from pathlib import Path
from typing import Any


class VectorStoreUnavailable(RuntimeError):
    """Raised when Chroma is not installed or cannot be initialized."""


class ChromaMemoryStore:
    def __init__(self, persist_dir: str | Path, collection_name: str = "local_ai_memory") -> None:
        self.persist_dir = Path(persist_dir).expanduser()
        self.collection_name = collection_name
        self._client: Any | None = None
        self._collection: Any | None = None

    def connect(self) -> bool:
        try:
            import chromadb
        except Exception:
            return False
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(self.collection_name)
        return True

    def add_text(self, doc_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        if self._collection is None and not self.connect():
            raise VectorStoreUnavailable("Chroma is unavailable. Run scripts/install_core.sh.")
        self._collection.add(ids=[doc_id], documents=[text], metadatas=[metadata or {}])

    def retrieve(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._collection is None and not self.connect():
            return []
        result = self._collection.query(query_texts=[query], n_results=limit)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        return [{"text": text, "metadata": metadata} for text, metadata in zip(documents, metadatas, strict=False)]
