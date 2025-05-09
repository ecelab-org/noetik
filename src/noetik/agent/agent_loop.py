"""Main orchestration loop for Noetik."""

from __future__ import annotations

import logging

from noetik.agent.planner_interface import load_planner
from noetik.agent.schema import AgentTurn
from noetik.agent.tool_executor import (
    ToolExecutionError,
    execute_tool,
)
from noetik.tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Agent Loop
# ---------------------------------------------------------------------------
def run_cli() -> None:
    """
    Run the main agent loop in CLI mode.
    This is a simple REPL that takes user input, sends it to the planner, executes any tool calls,
    and returns the final answer.
    """
    print("🔮  Noetik shell - type 'exit' to quit.")
    while True:
        # Load the planner
        planner = load_planner()
        user_msg = input("you> ").strip()
        if user_msg.lower() in {"exit", "quit"}:
            break

        # Ask planner what to do
        tool_calls, direct_answer = planner.plan(user_msg, list(TOOL_REGISTRY.keys()))

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
