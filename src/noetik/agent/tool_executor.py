"""Dispatches tool calls registered in ``noetik.tools`` and wraps errors."""

import logging
from typing import (
    Any,
    Dict,
)

from noetik.tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)


class ToolExecutionError(RuntimeError):
    """Raised when a requested tool cannot run or fails."""


def execute_tool(name: str, args: Dict[str, Any] | None = None) -> Any:
    """
    Look up *name* in the registry and invoke it with *args*.

    Parameters
    ----------
    name:
        The registered tool name.
    args:
        Keyword arguments to pass verbatim to the tool function.  If *None*,
        an empty dict is assumed.

    Returns
    -------
    Any
        Whatever the tool function returns.

    Raises
    ------
    ToolExecutionError
        If the tool is missing or its invocation raises an exception.
    """

    if args is None:
        args = {}

    tool_fn = TOOL_REGISTRY.get(name)
    if tool_fn is None:
        raise ToolExecutionError(f"Tool '{name}' is not registered.")

    try:
        logger.debug("Executing tool '%s' with args=%s", name, args)
        return tool_fn(**args)
    except TypeError as exc:
        # Argument mismatch — give the caller a clean exception.
        logger.exception("Argument error while executing tool '%s'", name)
        raise ToolExecutionError(f"Invalid arguments for tool '{name}': {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error in tool '%s'", name)
        raise ToolExecutionError(f"Tool '{name}' raised an error: {exc}") from exc
