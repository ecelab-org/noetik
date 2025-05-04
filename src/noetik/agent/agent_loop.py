"""Main orchestration loop for Noetik."""

from __future__ import annotations

import logging
from typing import List

from noetik.agent.schema import (
    AgentTurn,
    ToolCall,
)
from noetik.agent.tool_executor import (
    ToolExecutionError,
    execute_tool,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Stub planner – replace with a real LLM later
# ---------------------------------------------------------------------------
def fake_planner(user_msg: str) -> tuple[List[ToolCall], str | None]:
    """
    Return a dummy plan:

    - If the user starts with '!', treat the rest as an echo request.
    - If the user starts with '#add', treat the rest as an addition request.
    - Otherwise, return a simple echo-free reply.
    """
    if user_msg.startswith("!"):
        return (
            [ToolCall(name="echo", args={"text": user_msg[1:].strip()})],
            None,  # no final answer yet
        )
    if user_msg.startswith("#add"):
        parts = user_msg[4:].strip().split()
        if len(parts) == 2:
            if not parts[0].isdigit() or not parts[1].isdigit():
                return ([], "Error: Need two numbers to add.")
            return (
                [ToolCall(name="add", args={"a": int(parts[0]), "b": int(parts[1])})],
                None,  # no final answer yet
            )
        return ([], "Error: Need exactly two numbers to add.")
    return ([], f"🤖 Echo-free reply: {user_msg}")


# ---------------------------------------------------------------------------
# Agent Loop
# ---------------------------------------------------------------------------
def run_cli() -> None:
    """
    Run the main agent loop in CLI mode.
    This is a simple REPL that takes user input, sends it to the planner,
    executes any tool calls, and returns the final answer.
    """
    print("🔮  Noetik shell - type 'exit' to quit.")
    while True:
        user_msg = input("you> ").strip()
        if user_msg.lower() in {"exit", "quit"}:
            break

        # Ask planner what to do
        tool_calls, direct_answer = fake_planner(user_msg)

        turn = AgentTurn(user_message=user_msg, tool_calls=tool_calls)

        # Execute any tool calls
        for call in turn.tool_calls:
            try:
                result = execute_tool(call.name, call.args)
                logger.info("Tool '%s' returned: %s", call.name, result)
                # Decide what to do with *result*:
                #   - feed back into planner (future feature)
                #   - collect for final render
                # For demo we just print:
                print(f"[{call.name}] {result}")
            except ToolExecutionError as exc:
                print(f"⚠️  {exc}")

        # If planner already gave a final answer, show it
        if direct_answer:
            print(direct_answer)

        # TODO: persist *turn* in memory, vector store, etc.


if __name__ == "__main__":
    run_cli()
