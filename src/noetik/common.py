"""Common utility functions for the project."""

from enum import Enum
from typing import Any


class AnsiColors(Enum):
    """
    ANSI color codes for terminal output.
    """

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[33m"
    BLUE = "\033[94m"


def colored_print(text: str, color: AnsiColors, *args: Any, **kwargs: Any) -> None:
    """
    Print text in color.

    Args:
        text: The text to print
        color: The color to use (AnsiColors enum)
        args: Additional positional arguments for print
        kwargs: Additional keyword arguments for print
    """
    print(f"{color}{text}\033[0m", *args, **kwargs)  # ANSI reset at the end
