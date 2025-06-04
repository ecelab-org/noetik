"""
Core API backend for Noetik.

This module provides all business logic through a RESTful API that's used by frontends.
It exposes the following endpoints:
- **GET /health**  - liveness probe for health checks.
- **POST /sessions** - create a new session, returns a session ID.
- **GET /sessions** - list all active sessions.
- **POST /agent**   - multi-turn interaction: {"message": "...", "session_id": "..."}
"""

import logging
import uuid
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware

from noetik.api.models import (
    MessageRequest,
    MessageResponse,
    SessionResponse,
)
from noetik.common import (
    AnsiColors,
    colored_print,
)
from noetik.config import settings
from noetik.core.planner import load_planner
from noetik.core.schema import AgentTurn
from noetik.core.tool_executor import (
    ToolExecutionError,
    execute_tool,
)
from noetik.memory.memory_store import save_turn
from noetik.memory.vector_memory import VectorMemory
from noetik.tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)

# Session storage (in-memory for now, could be moved to a database)
sessions: Dict[str, List[str]] = {}

# Initialize vector memory
retriever = VectorMemory(host=settings.VECTOR_DB_HOST, port=settings.VECTOR_DB_PORT)

app = FastAPI(title="Noetik API", version="0.1.0", description="Noetik AI orchestrator API")

# Add CORS middleware to allow requests from the web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.WEBUI_PORT}",
        "http://localhost:{settings.API_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create a new one."""
    if session_id and session_id in sessions:
        return session_id

    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = []
    return new_session_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """Return a simple liveness payload."""
    return {"status": "ok"}


@app.post("/sessions", response_model=SessionResponse, summary="Create a new session")
async def create_session() -> SessionResponse:
    """Create a new conversation session."""
    session_id = get_or_create_session()
    return SessionResponse(session_id=session_id)


@app.get("/sessions", response_model=List[str], summary="List active sessions")
async def list_sessions() -> List[str]:
    """List all active session IDs."""
    return list(sessions.keys())


@app.post("/agent", response_model=MessageResponse, summary="Process a message")
async def agent_endpoint(req: MessageRequest) -> MessageResponse:
    """Process a user message with optional session context."""
    # Get or create a session
    session_id = get_or_create_session(req.session_id)
    session_history = sessions.get(session_id, [])

    # Get vector search results for context
    similar_contexts = list(retriever.query(req.message, k=3))

    # Build prompt with context from history and vector search
    prompt_parts: List[str] = []

    # Add vector search results first, clearly labeled
    if similar_contexts:
        prompt_parts.append(
            "RELEVANT INFORMATION FROM PAST CONVERSATIONS:\n" + "\n\n".join(similar_contexts)
        )

    # Add conversation history in chronological order
    if session_history:
        prompt_parts.append("PREVIOUS CONVERSATION:\n" + "\n".join(session_history[-3:]))

    # Join everything with clear separators
    context_block = "\n\n" + "\n\n".join(prompt_parts) + "\n\n" if prompt_parts else ""
    prompt_input = f"{context_block}CURRENT QUERY:\n{req.message}" if prompt_parts else req.message

    # Log the prompt input for debugging
    logger.debug("Prompt input for planning:\n%s", prompt_input)

    # Load the planner and process the request
    planner = load_planner()
    tool_calls, direct_answer = planner.plan(
        user_msg=prompt_input, available_tools=list(TOOL_REGISTRY.keys())
    )

    if not tool_calls and not direct_answer:
        direct_answer = "⚠️ Planner returned nothing."

    # Create an agent turn for recording history
    turn = AgentTurn(user_message=req.message, tool_calls=tool_calls)

    # Execute any tool calls
    tool_results: Dict[str, Any] = {}
    tool_outputs: List[str] = []

    for call in tool_calls:
        try:
            result = execute_tool(call.name, call.args)
            tool_results[call.name] = result
            tool_outputs.append(f"[{call.name}] {result}")
        except ToolExecutionError as exc:
            logger.warning("Tool failure: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Determine the final reply
    reply = direct_answer or "\n".join(str(v) for v in tool_results.values())

    # Save the turn to memory
    save_turn(turn, reply)

    # Save reply to session history
    session_text = f"User: {req.message}\nAssistant: {reply}"
    sessions[session_id].append(session_text)

    return MessageResponse(reply=reply, tool_results=tool_results or None, session_id=session_id)


@app.get("/", summary="API root")
async def root() -> dict[str, str]:
    """Return a simple welcome message."""
    return {"message": "Welcome to the Noetik API! Use /docs for API documentation."}


@app.get("/docs", include_in_schema=False)
async def get_docs() -> dict[str, str]:
    """Redirect to the OpenAPI docs."""
    return {"message": "Visit /docs for API documentation."}


# ---------------------------------------------------------------------------
# Public helper to launch the API (imported by main.py)
# ---------------------------------------------------------------------------
def run_api(
    host: str = "0.0.0.0", port: int = 8000, reload: bool = False, log_level: str | None = None
) -> None:
    """Start a uvicorn server hosting *app*.

    Parameters
    ----------
    host, port:
        Bind address for the HTTP server.
    reload:
        If *True*, enable auto-reload (useful in dev docker-compose).
    log_level:
        Logging level to use (default from settings if not provided).
    Raises
    """

    # Lazy import - keeps uvicorn an optional dependency at pkg‑import time
    import uvicorn  # pylint: disable=import-outside-toplevel

    if log_level is None:  # Use the default from settings if not provided
        log_level = settings.LOG_LEVEL

    logger.info(
        "Starting Noetik API at %s:%d (reload=%s, log_level=%s)", host, port, reload, log_level
    )

    try:
        # Ensure the vector memory is initialized
        retriever.init()
        logger.info("Vector memory initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize vector memory: %s", exc)
        raise RuntimeError("Failed to initialize vector memory") from exc

    # Start the API server
    logger.debug("API settings: %s", settings.model_dump())  # Log settings for debugging

    colored_print(
        "🔮 Noetik API is running at http://localhost:8000.",
        AnsiColors.GREEN,
    )
    colored_print(
        "Visit http://localhost:8000/docs for API documentation.",
        AnsiColors.BLUE,
    )
    uvicorn.run(
        "noetik.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


# ---------------------------------------------------------------------------
# `python -m noetik.api.app` helper
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_api(reload=True)
