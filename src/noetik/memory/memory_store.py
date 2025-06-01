"""Persist AgentTurn to vector DB + lightweight JSON log."""

import json
import uuid
from pathlib import Path

from noetik.agent.schema import AgentTurn
from noetik.memory.vector_memory import VectorMemory

_LOG_PATH = Path("/data/noetik_turns.jsonl")

_vector_mem = VectorMemory()


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
