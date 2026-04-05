"""
routers/memory.py
-----------------
Memory management endpoints.

GET    /api/memories/{user_id}            → list all memories for a user
DELETE /api/memories/{user_id}            → wipe all memories for a user
DELETE /api/memories/{user_id}/{memory_id} → delete a single memory
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from memory_service import MemoryService, get_memory_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["memory"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class MemoryItem(BaseModel):
    id: str | None = None
    memory: str
    score: float | None = None
    metadata: dict | None = None


class MemoryListResponse(BaseModel):
    user_id: str
    count: int
    memories: list[dict]


class DeleteResponse(BaseModel):
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/memories/{user_id}", response_model=MemoryListResponse)
async def get_memories(
    user_id: str,
    mem: MemoryService = Depends(get_memory_service),
) -> MemoryListResponse:
    """
    Return all stored memories for a user.
    Powers the live memory panel in the React frontend.
    """
    logger.info("GET /memories/%s", user_id)

    try:
        memories = mem.get_all(user_id=user_id)
    except Exception as exc:
        logger.exception("get_all() failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return MemoryListResponse(
        user_id=user_id,
        count=len(memories),
        memories=memories,
    )


@router.delete("/memories/{user_id}", response_model=DeleteResponse)
async def delete_all_memories(
    user_id: str,
    mem: MemoryService = Depends(get_memory_service),
) -> DeleteResponse:
    """
    Wipe every memory for a user.
    Triggered by the "Forget everything" button in the UI.
    """
    logger.info("DELETE /memories/%s  (all)", user_id)

    try:
        mem.delete_all(user_id=user_id)
    except Exception as exc:
        logger.exception("delete_all() failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return DeleteResponse(
        success=True,
        message=f"All memories for user '{user_id}' have been deleted.",
    )


@router.delete("/memories/{user_id}/{memory_id}", response_model=DeleteResponse)
async def delete_memory(
    user_id: str,
    memory_id: str,
    mem: MemoryService = Depends(get_memory_service),
) -> DeleteResponse:
    """
    Delete a single memory by its ID.
    Triggered when the user clicks the trash icon next to a memory in the UI.
    """
    logger.info("DELETE /memories/%s/%s", user_id, memory_id)

    try:
        mem.delete(memory_id=memory_id)
    except Exception as exc:
        logger.exception("delete() failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return DeleteResponse(
        success=True,
        message=f"Memory '{memory_id}' deleted.",
    )
