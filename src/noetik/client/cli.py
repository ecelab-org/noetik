"""CLI client for Noetik API."""

from __future__ import annotations

import logging
from typing import (
    Any,
    Dict,
    Tuple,
    cast,
)

import httpx

from noetik.common import (
    AnsiColors,
    colored_print,
)
from noetik.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CLI Client
# ---------------------------------------------------------------------------
def get_user_message() -> Tuple[str, bool]:
    """
    Get a message from the user via standard input.

    Returns:
        Tuple of (user_input, success_flag)
        The success_flag is False if input couldn't be read (e.g., Ctrl+C)
    """
    import signal  # pylint: disable=import-outside-toplevel

    # Ensure SIGINT breaks out of slow system calls such as read()
    # (True  ⇒  *do* interrupt;  False ⇒ restart them)
    signal.siginterrupt(signal.SIGINT, True)

    try:
        user_input = input().strip()
        return user_input, True
    except (EOFError, KeyboardInterrupt):
        return "", False


def call_api(endpoint: str, data: Dict[str, Any], max_retries: int = 5) -> Dict[str, Any]:
    """Make a POST request to the API and return the response with retries."""
    api_url = f"http://localhost:{settings.API_PORT}{endpoint}"

    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(api_url, json=data)
                response.raise_for_status()
                return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            # On connection refused, retry with exponential backoff
            if isinstance(e, httpx.ConnectError) and attempt < max_retries - 1:
                retry_delay = 0.5 * (2**attempt)  # exponential backoff: 0.5s, 1s, 2s, 4s...
                logger.info(
                    "API not ready yet, retrying in %.1f seconds (attempt %d/%d)...",
                    retry_delay,
                    attempt + 1,
                    max_retries,
                )
                import time  # pylint: disable=import-outside-toplevel

                time.sleep(retry_delay)
                continue

            # If we reached max retries or it's not a connection issue
            logger.error("API request error: %s", str(e))
            error_msg = f"Error connecting to API: {str(e)}"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = f"API error: {error_data['detail']}"
            except Exception:  # pylint: disable=broad-except
                pass
            colored_print(error_msg, AnsiColors.RED)
            return {"reply": error_msg}

    # If we've exhausted all retries without returning or raising an exception
    error_msg = f"Failed to connect to API after {max_retries} attempts"
    colored_print(error_msg, AnsiColors.RED)
    return {"reply": error_msg}


def run_cli() -> None:
    """Run the CLI client that communicates with the API."""
    # Create a new session
    session_response = call_api("/sessions", {})
    session_id = session_response.get("session_id")

    if not session_id:
        colored_print("⚠️ Failed to create a session", AnsiColors.RED)
        return

    colored_print("\n🔮 Noetik shell - type 'exit' or 'quit' (or Ctrl+C) to exit", AnsiColors.GREEN)
    while True:
        colored_print("\n🧑 You: ", AnsiColors.BLUE, end="")
        user_msg, ok = get_user_message()
        if not ok:
            break  # Exit if user input couldn't be retrieved (e.g., Ctrl+C)
        if user_msg.lower() in {"exit", "quit"}:
            break

        # Send message to API
        response = call_api("/agent", {"message": user_msg, "session_id": session_id})

        # Display the response
        if "tool_results" in response and response["tool_results"]:
            for tool_name, result in response["tool_results"].items():
                colored_print(f"[{tool_name}] {result}", AnsiColors.GREEN)

        colored_print(response.get("reply", "No response from API"), AnsiColors.YELLOW)


if __name__ == "__main__":
    run_cli()
