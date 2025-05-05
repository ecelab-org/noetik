"""
Minimal FastAPI stub for Noetik.

This stub exposes two endpoints:
- **GET /health**  - liveness probe for Docker / k8s.
- **POST /agent**   - single-turn interaction: {"message": "..."}

It shares the same planner and tool-execution path as the CLI and exposes a convenient ``run_api``
helper so the entry-point can import it directly.
"""

import logging
from typing import (
    Any,
    Dict,
)

from fastapi import (
    FastAPI,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from noetik.agent.agent_loop import fake_planner  # reuse stub planner
from noetik.agent.tool_executor import (
    ToolExecutionError,
    execute_tool,
)

logger = logging.getLogger(__name__)
app = FastAPI(title="Noetik API Stub", version="0.1.0")


# ---------------------------------------------------------------------------
# Pydantic request / response schema
# ---------------------------------------------------------------------------
class MessageRequest(BaseModel):
    """Incoming user message for single-turn interaction."""

    message: str = Field(..., description="User message for Noetik")


class MessageResponse(BaseModel):
    """API response returned to the caller."""

    reply: str
    tool_results: Dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:  # noqa: D401 – simple function
    """Return a simple liveness payload."""

    return {"status": "ok"}


@app.post("/agent", response_model=MessageResponse, summary="Single-turn agent")
async def agent_endpoint(req: MessageRequest) -> MessageResponse:  # noqa: D401
    """Process a single user message.

    For now, mirrors the CLI design (single planner call + optional tool call).
    """

    tool_calls, direct_answer = fake_planner(req.message)
    tool_results: dict[str, Any] = {}

    for call in tool_calls:
        try:
            tool_results[call.name] = execute_tool(call.name, call.args)
        except ToolExecutionError as exc:
            logger.warning("Tool failure: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    reply = direct_answer or " ".join(str(v) for v in tool_results.values())
    return MessageResponse(reply=reply, tool_results=tool_results or None)


# ---------------------------------------------------------------------------
# Public helper to launch the API (imported by main.py)
# ---------------------------------------------------------------------------


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Start a uvicorn server hosting *app*.

    Parameters
    ----------
    host, port:
        Bind address for the HTTP server.
    reload:
        If *True*, enable auto-reload (useful in dev docker-compose).
    """

    # Lazy import - keeps uvicorn an optional dependency at pkg‑import time
    import uvicorn  # pylint: disable=import-outside-toplevel

    uvicorn.run("noetik.web.api:app", host=host, port=port, reload=reload)


# ---------------------------------------------------------------------------
# `python -m noetik.web.api` helper
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_api(reload=True)
