"""
Schema definitions for planner <-> agent <-> tool messages.

These data models serve as the contract between the planner LLM, the orchestration loop, and
individual tools.  We keep them separate from runtime logic so they can be imported anywhere without
side-effects.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)


class ToolCall(BaseModel):
    """A call that the planner wants the agent to execute."""

    name: str = Field(..., description="Registered tool name")
    args: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments for the tool")


class PlannerThought(BaseModel):
    """Optional scratchpad text from the planner (chain-of-thought)."""

    content: str


class AgentTurn(BaseModel):
    """A single turn in the agent loop (for logging / memory)."""

    user_message: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    planner_response: Optional[str] = None  # Final user‑facing answer
    thoughts: Optional[List[PlannerThought]] = None
