"""
memory_service.py
-----------------
Core memory layer for MemChat, powered by Mem0.

Handles:
  - Adding new memories from user/assistant messages
  - Searching relevant memories for a given query
  - Fetching the full memory history for a user
  - Deleting individual or all memories for a user

LLM      : Google Gemini (gemini-2.5-flash)
Embeddings: Gemini text-embedding-004
Vector DB : Qdrant (local, on-disk)
"""

import os
import logging
from typing import Any

from mem0 import Memory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mem0 configuration
# ---------------------------------------------------------------------------

def _build_mem0_config() -> dict:
    """
    Assemble the Mem0 config dict from environment variables.

    Required env vars:
        GEMINI_API_KEY   — Google AI Studio key (free tier works fine)
        QDRANT_PATH      — Absolute path where Qdrant stores its on-disk data
                           e.g. "/app/qdrant_storage"

    Optional env vars:
        QDRANT_COLLECTION — Collection name inside Qdrant (default: "memchat")
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")

    qdrant_path = os.environ.get("QDRANT_PATH", "./qdrant_storage")
    collection_name = os.environ.get("QDRANT_COLLECTION", "memchat")

    return {
        # ── LLM ──────────────────────────────────────────────────────────────
        "llm": {
            "provider": "gemini",
            "config": {
                "model": "gemini-2.5-flash",
                "api_key": gemini_api_key,
                "temperature": 0.1,   # low temp → consistent memory extraction
                "max_tokens": 2000,
            },
        },
        # ── Embeddings ───────────────────────────────────────────────────────
        "embedder": {
            "provider": "gemini",
            "config": {
                "model": "models/gemini-embedding-001",
                "api_key": gemini_api_key,
            },
        },
        # ── Vector store (Qdrant, local on-disk) ─────────────────────────────
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": collection_name,
                "path": qdrant_path,        # on-disk persistence; no server needed
                "on_disk": True,
                "embedding_model_dims": 768,
            },
        },
        # ── Memory behaviour ─────────────────────────────────────────────────
        "version": "v1.1",                  # enables graph-free structured memory
    }


# ---------------------------------------------------------------------------
# MemoryService
# ---------------------------------------------------------------------------

class MemoryService:
    """
    Thin wrapper around Mem0's Memory client.

    All operations are scoped to a `user_id` so that memories are fully
    isolated per user — exactly what you'd want in a multi-user chat app.
    """

    def __init__(self) -> None:
        config = _build_mem0_config()
        self._mem = Memory.from_config(config)
        logger.info("Mem0 Memory client initialised successfully.")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add(
        self,
        messages: list[dict[str, str]],
        user_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        """
        Extract and store memories from a list of chat messages.

        Args:
            messages:  OpenAI-style message list, e.g.
                       [{"role": "user", "content": "I love hiking."}]
            user_id:   Stable identifier for the user (e.g. UUID or username).
            metadata:  Optional extra fields stored alongside each memory
                       (e.g. {"session_id": "abc123"}).

        Returns:
            Mem0's raw response dict (contains the list of added memories).
        """
        kwargs: dict[str, Any] = {"user_id": user_id}
        if metadata:
            kwargs["metadata"] = metadata

        result = self._mem.add(messages, **kwargs)
        logger.debug("add() → user=%s  result=%s", user_id, result)
        return result

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Retrieve the most relevant memories for a query (semantic search).

        Args:
            query:    The user's current message / intent.
            user_id:  Scope the search to this user's memories only.
            limit:    Maximum number of memories to return (default 5).

        Returns:
            List of memory dicts, each containing at minimum:
              - "id"      : memory UUID
              - "memory"  : the extracted memory string
              - "score"   : similarity score (0–1, higher = more relevant)
        """
        results = self._mem.search(query, user_id=user_id, limit=limit)
        # Mem0 v1.1 returns {"results": [...]}; flatten for convenience
        memories = results.get("results", results) if isinstance(results, dict) else results
        logger.debug("search() → user=%s  query=%r  hits=%d", user_id, query, len(memories))
        return memories

    def get_all(self, user_id: str) -> list[dict]:
        """
        Fetch every stored memory for a user (for the memory panel in the UI).

        Returns:
            List of all memory dicts for the given user.
        """
        results = self._mem.get_all(user_id=user_id)
        memories = results.get("results", results) if isinstance(results, dict) else results
        logger.debug("get_all() → user=%s  count=%d", user_id, len(memories))
        return memories

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, memory_id: str) -> dict:
        """
        Delete a single memory by its UUID.

        Args:
            memory_id: The "id" field returned by search() or get_all().

        Returns:
            Mem0's deletion response.
        """
        result = self._mem.delete(memory_id)
        logger.debug("delete() → memory_id=%s", memory_id)
        return result

    def delete_all(self, user_id: str) -> dict:
        """
        Wipe all memories for a user (e.g. "forget everything" button in UI).

        Args:
            user_id: The user whose memories should be erased.

        Returns:
            Mem0's deletion response.
        """
        result = self._mem.delete_all(user_id=user_id)
        logger.info("delete_all() → user=%s  ALL memories cleared.", user_id)
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
# Import this instance in your FastAPI routers:
#
#   from memory_service import memory_service
#
# Initialisation is deferred to first import so that env vars can be
# injected before the module is loaded (e.g. via python-dotenv in main.py).

memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """
    FastAPI dependency that returns (and lazily initialises) the singleton.

    Usage in a router:
        from fastapi import Depends
        from memory_service import get_memory_service, MemoryService

        @router.post("/chat")
        async def chat(
            body: ChatRequest,
            mem: MemoryService = Depends(get_memory_service),
        ):
            memories = mem.search(body.message, user_id=body.user_id)
            ...
    """
    global memory_service
    if memory_service is None:
        memory_service = MemoryService()
    return memory_service
