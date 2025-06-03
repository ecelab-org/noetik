"""
Noetik entry point.

This file handles startup concerns (arg-parsing, env setup, logging) and launches the appropriate
interface (API, CLI, or Web UI).
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from noetik.api.app import run_api
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
    # Reduce chromadb log level to WARNING or ERROR
    logging.getLogger("httpx").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    """
    Main entry point for the Noetik application.

    This function sets up the command-line interface, initializes logging, and starts the
    application in either CLI, API, or web mode.
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
        choices=["cli", "api", "web"],
        default="cli",
        help="Launch interactive CLI, REST API, or web interface (default: cli)",
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

    if args.mode == "api":
        # Run only the API server
        run_api(host="0.0.0.0", port=settings.API_PORT, reload=settings.DEBUG)

    else:
        # Run both API and either CLI or web UI
        if args.mode not in ["cli", "web"]:
            parser.error(f"Unknown mode: {args.mode}")

        # Lazy import to avoid web dependencies if not needed
        import threading  # pylint: disable=import-outside-toplevel

        # Start API server in a separate thread
        api_thread = threading.Thread(
            target=run_api,
            kwargs={
                "host": "0.0.0.0",
                "port": settings.API_PORT,
                "reload": False,  # Reload doesn't work well with threading
            },
            daemon=True,
        )
        api_thread.start()

        if args.mode == "cli":
            # Lazy import to avoid CLI dependencies if not needed
            from noetik.client.cli import (  # pylint: disable=import-outside-toplevel
                run_cli,
            )

            # Run CLI in main thread
            run_cli()
        elif args.mode == "web":
            # Lazy import to avoid web dependencies if not needed
            from noetik.client.webapp import (  # pylint: disable=import-outside-toplevel
                run_webapp,
            )

            # Run web UI in main thread
            run_webapp(reload=settings.DEBUG)


if __name__ == "__main__":
    main()
