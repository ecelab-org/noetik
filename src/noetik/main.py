"""
Noetik entry point.

This file keeps startup concerns (arg-parsing, env setup, logging) separate from the agent logic so
``agent_loop.py`` remains unit-testable.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from noetik.agent.agent_loop import run_cli
from noetik.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:  # noqa: WPS231 (acceptable complexity)
    """
    Main entry point for the Noetik application.

    This function sets up the command-line interface, initializes logging, and starts the
    application in either CLI or API mode.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Ensure the data directory exists
    data_dir = Path(settings.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    # Ensure the data directory is writable
    if not data_dir.is_dir() or not os.access(data_dir, os.W_OK):
        logger.error("Data directory is not writable: %s", data_dir)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Run Noetik AI orchestrator")
    parser.add_argument(
        "--mode",
        choices=["cli", "api"],
        default="cli",
        help="Launch interactive CLI or REST API stub (default: cli)",
    )
    parser.add_argument(
        "--log-level",
        default=settings.LOG_LEVEL,
        help="Logging level (default from env: %(default)s)",
    )
    args = parser.parse_args(argv)

    _init_logging(args.log_level)

    logger.info("Starting Noetik [%s mode]", args.mode)
    logger.debug("Settings: %s", settings.model_dump())

    if args.mode == "cli":
        run_cli()
    elif args.mode == "api":
        # Lazy import to avoid uvicorn dep if not needed
        from noetik.web.api import run_api  # pylint: disable=import-outside-toplevel

        run_api()
    else:
        parser.error(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
