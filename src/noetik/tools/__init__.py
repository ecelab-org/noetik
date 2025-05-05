"""
Tool registry for Noetik.
This module provides a decorator to register tools and a registry to look them up by name.
The tools are functions that can be called with keyword arguments and return a value.
"""

import logging
from typing import (
    Callable,
    Dict,
)

TOOL_REGISTRY: Dict[str, Callable] = {}
"""Global registry of tool functions."""


def register_tool(name: str) -> Callable:
    """
    Register a tool function with the given name.
    The name must be unique and is used to look up the function in the registry.  The function must
    accept keyword arguments and return a value.

    The function is registered as a decorator, so it can be used like this:
        @register_tool("my_tool")
        def my_tool_function(arg1, arg2):
            # Do something
            return result

    The function will be added to the TOOL_REGISTRY dictionary with the name as the key.  If a
    function with the same name is already registered, a ValueError will be raised.

    Parameters
    ----------
    name: str
        The name of the tool.  This must be unique and is used to look up the
        function in the registry.
    Returns
    -------
    Callable
        A decorator that registers the function with the given name.
    Raises
    ------
    ValueError
        If a function with the same name is already registered.
    """
    if name in TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' is already registered.")
    logger = logging.getLogger(__name__)
    logger.debug("Registering tool '%s'", name)

    def wrapper(fn: Callable) -> Callable:
        TOOL_REGISTRY[name] = fn
        return fn

    return wrapper


@register_tool("echo")
def echo_tool(text: str) -> str:
    """Echo the input text back to the caller."""
    return text
