"""
chat_service.py
---------------
Handles the LLM turn for MemChat.

Responsibilities:
  1. Retrieve relevant memories from Mem0 (via MemoryService.search)
  2. Build a context-aware system prompt that injects those memories
  3. Call Gemini (gemini-2.5-flash) via google-genai SDK
  4. Persist the new user+assistant turn back into Mem0

Flow per chat turn:
    user message
        │
        ▼
    search memories  ──→  [mem1, mem2, ...]
        │
        ▼
    build prompt  (system prompt + memories + conversation history)
        │
        ▼
    call Gemini  ──→  assistant reply
        │
        ▼
    add [user msg, assistant reply] to Mem0
        │
        ▼
    return reply + memories used
"""

import logging
import os
from typing import Any

from google import genai
from google.genai import types

from memory_service import MemoryService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_BASE_SYSTEM_PROMPT = """You are MemChat, a helpful and friendly AI assistant with persistent memory.

You remember details about the user across conversations — their preferences, past topics, \
and anything they've shared before. When relevant memories exist, you reference them \
naturally (don't announce "I found a memory about you"; just use the knowledge).

{memory_block}

Guidelines:
- Be warm, concise, and genuinely helpful.
- If the user shares new information about themselves, acknowledge it naturally.
- Never fabricate memories. Only reference what's in the memory block above.
- If no memories are relevant, just answer the question normally.
"""

_MEMORY_BLOCK_TEMPLATE = """## What you remember about this user:
{memories}"""

_NO_MEMORY_BLOCK = "## Memory: No relevant memories found for this conversation yet."


def _format_memory_block(memories: list[dict]) -> str:
    """Turn a list of Mem0 memory dicts into a readable block for the prompt."""
    if not memories:
        return _NO_MEMORY_BLOCK

    lines = []
    for i, mem in enumerate(memories, 1):
        text = mem.get("memory", "")
        score = mem.get("score")
        score_str = f"  [relevance: {score:.2f}]" if score is not None else ""
        lines.append(f"{i}. {text}{score_str}")

    return _MEMORY_BLOCK_TEMPLATE.format(memories="\n".join(lines))


def _build_system_prompt(memories: list[dict]) -> str:
    memory_block = _format_memory_block(memories)
    return _BASE_SYSTEM_PROMPT.format(memory_block=memory_block)


# ---------------------------------------------------------------------------
# ChatService
# ---------------------------------------------------------------------------

class ChatService:
    """
    Orchestrates one full chat turn:
      search → prompt → LLM → persist → return
    """

    def __init__(self, memory_service: MemoryService) -> None:
        self._mem = memory_service
        self._init_gemini()

    def _init_gemini(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")
        self._client = genai.Client(api_key=api_key)
        self._model_name = "gemini-2.5-flash"
        logger.info("Gemini configured with model: %s", self._model_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(
        self,
        user_id: str,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_limit: int = 5,
    ) -> dict[str, Any]:
        """
        Process one user message and return the assistant's reply.

        Args:
            user_id:      Stable user identifier (scopes Mem0 memories).
            message:      The user's current message.
            history:      Prior turns in OpenAI format, e.g.:
                          [{"role": "user", "content": "..."}, ...]
                          Pass [] or None for a fresh session.
            memory_limit: How many memories to inject (default 5).

        Returns:
            {
                "reply":           str,         # assistant's response
                "memories_used":   list[dict],  # memories injected into prompt
                "memories_added":  dict,        # Mem0 add() response
            }
        """
        history = history or []

        # ── 1. Retrieve relevant memories ────────────────────────────────────
        memories = self._mem.search(message, user_id=user_id, limit=memory_limit)
        logger.info(
            "chat() user=%s  memories_found=%d  message=%r",
            user_id, len(memories), message[:80],
        )

        # ── 2. Build system prompt with memory context ────────────────────────
        system_prompt = _build_system_prompt(memories)

        # ── 3. Call Gemini ────────────────────────────────────────────────────
        reply = self._call_gemini(
            system_prompt=system_prompt,
            history=history,
            user_message=message,
        )

        # ── 4. Persist the new turn into Mem0 ────────────────────────────────
        new_turn = [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": reply},
        ]
        added = self._mem.add(new_turn, user_id=user_id)

        return {
            "reply":          reply,
            "memories_used":  memories,
            "memories_added": added,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_gemini(
        self,
        system_prompt: str,
        history: list[dict[str, str]],
        user_message: str,
    ) -> str:
        """
        Send a request to Gemini and return the text response.
        Uses the new google-genai SDK (google.genai.Client).
        """
        # Convert history: OpenAI "assistant" → Gemini "model"
        gemini_history = []
        for turn in history:
            role = "model" if turn["role"] == "assistant" else "user"
            gemini_history.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=turn["content"])],
                )
            )

        # Add the current user message
        gemini_history.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_message)],
            )
        )

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=gemini_history,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=2048,
            ),
        )

        reply = response.text.strip()
        logger.debug("Gemini reply: %r", reply[:120])
        return reply


# ---------------------------------------------------------------------------
# Module-level singleton + FastAPI dependency
# ---------------------------------------------------------------------------

_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """
    FastAPI dependency. Lazily creates the ChatService singleton,
    reusing the MemoryService singleton from memory_service.py.
    """
    global _chat_service
    if _chat_service is None:
        from memory_service import get_memory_service
        _chat_service = ChatService(get_memory_service())
    return _chat_service
