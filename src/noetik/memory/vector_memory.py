"""
Thin wrapper around Chroma for storing & querying text chunks.

We store each `AgentTurn` as one document:
  text     = user_msg + assistant_reply (+ tool outputs)
  metadata = { "turn_id": int, "role": "turn" }
"""

import logging
import os
from typing import (
    List,
    cast,
)

import chromadb
from chromadb.api.types import EmbeddingFunction
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

_DEFAULT_EMBED_MODEL = os.getenv("NOETIK_EMBED_MODEL", "all-MiniLM-L6-v2")  # small; runs CPU‑only


class VectorMemory:
    """
    Chroma wrapper for storing & querying text chunks.
    """

    def __init__(
        self,
        collection_name: str = "noetik",
        persist: bool = True,
        host: str = "chroma",  # service name in docker‑compose
        port: int = 8000,
    ):
        self._client = chromadb.HttpClient(host=host, port=port)
        self._embed_fn: EmbeddingFunction = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=_DEFAULT_EMBED_MODEL
            )
        )

        # Implement the persist parameter logic
        if not persist:
            # Delete the collection if it exists (non-persistent mode)
            try:
                self._client.delete_collection(collection_name)
                logger.info(
                    "Deleted existing collection '%s' (non-persistent mode)", collection_name
                )
            except Exception as e:  # pylint: disable=broad-except
                # Collection might not exist yet, which is fine
                logger.debug("Could not delete collection '%s': %s", collection_name, str(e))

        # Create or get the collection
        self._col = self._client.get_or_create_collection(
            name=collection_name, embedding_function=cast(EmbeddingFunction, self._embed_fn)
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        """Add or upsert a single document."""
        self._col.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def query(self, text: str, k: int = 5) -> List[str]:
        """Return top-k docs (raw text) similar to `text`."""
        res = self._col.query(
            query_texts=[text],
            n_results=k,
            include=["documents"],
        )
        logger.info("Memory query results: '%s'", res)
        if res and "documents" in res and res["documents"]:
            return res["documents"][0]  # List[str]
        return []

    # Convenience for tests / admin
    def count(self) -> int:
        """Return number of documents in the collection."""
        return self._col.count()
