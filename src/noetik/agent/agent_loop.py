"""Main orchestration loop for Noetik."""

from __future__ import annotations

import logging
from typing import Tuple

from noetik.agent.planner_interface import load_planner
from noetik.agent.schema import AgentTurn
from noetik.agent.tool_executor import (
    ToolExecutionError,
    execute_tool,
)
from noetik.common import (
    AnsiColors,
    colored_print,
)
from noetik.memory.memory_store import save_turn
from noetik.memory.vector_memory import VectorMemory
from noetik.tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)
retriever = VectorMemory()


# ---------------------------------------------------------------------------
# Agent Loop
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


def run_cli() -> None:
    """Run the main agent loop in CLI mode."""
    colored_print("🔮  Noetik shell - type 'exit' to quit.", AnsiColors.YELLOW)
    session_history: list[str] = []  # Store recent conversations in memory

    while True:
        # Load the planner
        planner = load_planner()
        colored_print("\n🧑 You: ", AnsiColors.BLUE, end="")
        user_msg, ok = get_user_message()
        if not ok:
            break  # Exit if user input couldn't be retrieved (e.g., Ctrl+C)
        if user_msg.lower() in {"exit", "quit"}:
            break

        # Get vector search results
        similar_contexts = list(retriever.query(user_msg, k=3))

        # Build prompt with clear sections
        prompt_parts: list[str] = []

        # Add vector search results first, clearly labeled
        if similar_contexts:
            prompt_parts.append("RELEVANT INFORMATION:\n" + "\n\n".join(similar_contexts))

        # Add conversation history in chronological order
        if session_history:
            prompt_parts.append("PREVIOUS CONVERSATION:\n" + "\n".join(session_history[-3:]))

        # Join everything with clear separators
        context_block = "\n\n" + "\n\n".join(prompt_parts) + "\n\n"
        prompt_input = f"{context_block}CURRENT QUERY:\n{user_msg}" if prompt_parts else user_msg

        tool_calls, direct_answer = planner.plan(prompt_input, list(TOOL_REGISTRY.keys()))
        if not tool_calls and not direct_answer:
            direct_answer = "⚠️ Planner returned nothing."

        turn = AgentTurn(user_message=user_msg, tool_calls=tool_calls)

        # Execute any tool calls
        tool_outputs: list[str] = []
        if tool_calls:
            logger.info(
                "Planner returned %d tool calls: %s",
                len(turn.tool_calls),
                [call.name for call in tool_calls],
            )

            for call in turn.tool_calls:
                try:
                    result = execute_tool(call.name, call.args)
                    tool_outputs.append(f"[{call.name}] {result}")
                    logger.info("Tool '%s' returned: %s", call.name, result)
                    # Decide what to do with *result*:
                    #   - feed back into planner (future feature)
                    #   - collect for final render
                    # For demo we just print:
                    colored_print(f"[{call.name}] {result}", AnsiColors.GREEN)
                except ToolExecutionError as exc:
                    colored_print(f"⚠️ {exc}", AnsiColors.RED)

        save_turn(turn, direct_answer or "\n".join(tool_outputs))  # Save the turn to memory

        # If planner already gave a final answer, show it
        if direct_answer:
            colored_print(direct_answer, AnsiColors.YELLOW)

        # Save reply to session history
        joined_outputs = "\n".join(tool_outputs)
        session_text = f"User: {user_msg}\nAssistant: {direct_answer or joined_outputs}"
        session_history.append(session_text)


if __name__ == "__main__":
    run_cli()
