"""
Basic sanity tests for the tool executor.

Run with:
$ pytest -q
"""

from noetik.agent.tool_executor import (
    ToolExecutionError,
    execute_tool,
)
from noetik.tools import register_tool


# This is a stub tool for testing purposes.
@register_tool("add")
def _add(a: int, b: int) -> int:
    """Return the sum of two integers (used only for tests)."""

    return a + b


def test_execute_tool_success() -> None:
    """Executor should return the correct value when the tool is valid."""

    assert execute_tool("add", {"a": 2, "b": 3}) == 5


def test_execute_tool_missing() -> None:
    """Executor should raise *ToolExecutionError* for an unknown tool."""

    try:
        execute_tool("not_a_tool", {})
    except ToolExecutionError as exc:
        assert "not_a_tool" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("ToolExecutionError was not raised")


def test_execute_tool_bad_args() -> None:
    """Executor should raise *ToolExecutionError* for wrong arguments."""

    try:
        execute_tool("add", {"a": 2})  # missing 'b'
    except ToolExecutionError as exc:
        assert "Invalid arguments" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("ToolExecutionError was not raised")
