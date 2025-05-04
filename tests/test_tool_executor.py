"""Unit tests for the tool executor."""

from noetik.agent.tool_executor import (
    ToolExecutionError,
    execute_tool,
)


def test_execute_tool_bad_args() -> None:
    """Executor should raise *ToolExecutionError* for wrong arguments."""

    try:
        execute_tool("add", {"a": 2})  # missing 'b'
    except ToolExecutionError as exc:
        assert "Invalid arguments" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("ToolExecutionError was not raised")
