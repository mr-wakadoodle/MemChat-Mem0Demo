"""
routers/chat.py
---------------
POST /api/chat — the main chat endpoint.

Request  → ChatRequest  (user_id, message, history)
Response → ChatResponse (reply, memories_used, memories_added)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from chat_service import ChatService, get_chat_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class Message(BaseModel):
    """Single turn in a conversation (OpenAI-style)."""
    role: str = Field(..., examples=["user", "assistant"])
    content: str


class ChatRequest(BaseModel):
    user_id: str = Field(
        ...,
        description="Stable identifier for the user (e.g. UUID or username).",
        examples=["user_rahul"],
    )
    message: str = Field(
        ...,
        description="The user's current message.",
        examples=["What's a good hiking trail near me?"],
    )
    history: list[Message] = Field(
        default_factory=list,
        description=(
            "Prior conversation turns (oldest first). "
            "The frontend is responsible for maintaining this list."
        ),
    )
    memory_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Max number of memories to inject into the prompt.",
    )


class MemoryItem(BaseModel):
    """A single memory returned by Mem0."""
    id: str | None = None
    memory: str
    score: float | None = None


class ChatResponse(BaseModel):
    reply: str = Field(..., description="The assistant's response.")
    memories_used: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Memories retrieved from Mem0 and injected into the prompt.",
    )
    memories_added: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw Mem0 response from the add() call.",
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    svc: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Send a message and receive an AI reply enriched with persistent memory.

    - Searches Mem0 for memories relevant to the user's message.
    - Injects those memories into Gemini's system prompt.
    - Persists the new turn back to Mem0 after the reply is generated.
    """
    logger.info("POST /chat  user_id=%s  message=%r", body.user_id, body.message[:80])

    try:
        result = await svc.chat(
            user_id=body.user_id,
            message=body.message,
            history=[m.model_dump() for m in body.history],
            memory_limit=body.memory_limit,
        )
    except Exception as exc:
        logger.exception("chat() failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return ChatResponse(
        reply=result["reply"],
        memories_used=result["memories_used"],
        memories_added=result["memories_added"],
    )
