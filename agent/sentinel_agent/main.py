"""SentinelX Endpoint Agent — main entry point.

Usage:
    python -m sentinel_agent
"""

import asyncio
import logging
import sys

from datetime import UTC, datetime

from sentinel_agent.agent import SentinelAgent
from sentinel_agent.config import get_agent_settings


def setup_agent_logging(level: str = "INFO") -> None:
    """Configure agent logging (mirrors backend structured logging)."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass

    class AgentFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            lvl = record.levelname.ljust(8)
            return f"{timestamp} | {lvl} | {record.name} | {super().format(record)}"

    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric)
    handler.setFormatter(AgentFormatter())
    root.addHandler(handler)


def main() -> None:
    """Agent entry point: load config, init logging, run agent."""
    try:
        settings = get_agent_settings()
    except Exception as exc:
        print(f"[ERROR] Failed to load agent configuration: {exc}", file=sys.stderr)
        sys.exit(1)

    setup_agent_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    agent = SentinelAgent(settings)

    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        # Ensure clean shutdown
        if agent.is_running:
            asyncio.run(agent.stop())
    except Exception as exc:
        logger.error("Agent terminated with error: %s", exc)
        sys.exit(1)

    logger.info("Agent exited cleanly")


if __name__ == "__main__":
    main()
