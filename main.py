"""
main.py
-------
FastAPI application entry point for MemChat.

Handles:
  - Loading environment variables (via python-dotenv)
  - Lifespan: eagerly initialise Mem0 + Gemini on startup
  - CORS middleware (for the React frontend)
  - Router registration (/chat, /memories)
  - Health-check endpoint
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env before anything else so env vars are available to services
load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eagerly initialise singletons at startup so the first request isn't slow.
    Any misconfiguration (missing API key, bad Qdrant path) surfaces immediately.
    """
    logger.info("── MemChat startup ──────────────────────────────────")

    # Import here (after load_dotenv) so env vars are already set
    from memory_service import get_memory_service
    from chat_service import get_chat_service

    get_memory_service()   # initialises Mem0 + Qdrant
    get_chat_service()     # initialises Gemini

    logger.info("Memory service  ✓")
    logger.info("Chat service    ✓")
    logger.info("MemChat is ready  🧠")

    yield  # app runs here

    logger.info("── MemChat shutdown ─────────────────────────────────")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MemChat API",
    description=(
        "Persistent-memory AI chat powered by Mem0, Gemini, and Qdrant. "
        "Built to demonstrate Mem0's memory layer."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

# In production replace "*" with your actual frontend origin.
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173",   # CRA and Vite defaults
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from routers.chat import router as chat_router
from routers.memory import router as memory_router

app.include_router(chat_router,   prefix="/api")
app.include_router(memory_router, prefix="/api")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
async def health():
    """Simple liveness probe — returns 200 when the server is up."""
    return {"status": "ok", "service": "memchat-api"}


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,     # hot-reload for development
        log_level="info",
    )
