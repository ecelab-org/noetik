"""Persist AgentTurn to vector DB + lightweight JSON log."""

import json
import uuid
from pathlib import Path

from noetik.config import settings
from noetik.core.schema import AgentTurn
from noetik.memory.vector_memory import VectorMemory

_LOG_PATH = Path("/data/noetik_turns.jsonl")

_vector_mem = VectorMemory(host=settings.VECTOR_DB_HOST, port=settings.VECTOR_DB_PORT)


def init_memory_store() -> None:
    """
    Initialize the memory store by ensuring the log file exists.
    This is called at application startup to prepare the environment.
    """
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _LOG_PATH.exists():
        _LOG_PATH.touch()  # Create an empty file if it doesn't exist
    _vector_mem.init()  # Initialize vector memory connection


def save_turn(turn: AgentTurn, assistant_reply: str) -> None:
    """
    Save an AgentTurn to the log and vector DB.
    This function persists the turn in two ways:
    1. Appends to a flat-file audit trail (JSON lines format).
    2. Adds to a vector DB for similarity search.
    """
    # Flat‑file audit trail
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"turn": turn.model_dump(), "reply": assistant_reply}) + "\n")

    # Vector DB
    doc_id = str(uuid.uuid4())
    text = f"User: {turn.user_message}\nAssistant: {assistant_reply}"
    _vector_mem.add(doc_id, text, metadata={"role": "turn"})
