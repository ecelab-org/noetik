"""
Pydantic models for Noetik API requests and responses.
This module defines the request and response schemas used by the Noetik API.
"""

from typing import (
    Any,
    Dict,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)


# ---------------------------------------------------------------------------
# Pydantic request / response schema
# ---------------------------------------------------------------------------
class SessionRequest(BaseModel):
    """Request to create a new session."""

    pass  # pylint: disable=unnecessary-pass


class SessionResponse(BaseModel):
    """Response with session information."""

    session_id: str


class MessageRequest(BaseModel):
    """Incoming user message."""

    message: str = Field(..., description="User message for Noetik")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")


class MessageResponse(BaseModel):
    """API response returned to the caller."""

    reply: str
    tool_results: Dict[str, Any] | None = None
    session_id: str
