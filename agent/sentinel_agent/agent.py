"""SentinelX Endpoint Agent — core lifecycle management."""

import asyncio
import logging
import platform
import signal
import uuid
from datetime import UTC, datetime

from sentinel_agent import __version__
from sentinel_agent.config import AgentSettings

logger = logging.getLogger(__name__)


class SentinelAgent:
    """Core SentinelX endpoint agent.

    Manages the agent lifecycle: initialization, startup, event loop, and
    graceful shutdown. Module implementations (monitoring, classification,
    risk, policy, enforcement, transport, storage) will be plugged in
    during later phases.
    """

    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._session_id = str(uuid.uuid4())[:8]

    @property
    def device_id(self) -> str:
        """Return the configured device identifier."""
        return self._settings.DEVICE_ID

    @property
    def is_running(self) -> bool:
        """Check whether the agent is currently running."""
        return self._running

    def _display_startup_banner(self) -> None:
        """Print agent startup information to the console."""
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(
            f"\n"
            f"  +------------------------------------------+\n"
            f"  |         SentinelX Endpoint Agent         |\n"
            f"  |              v{__version__:<16}      |\n"
            f"  +------------------------------------------+\n"
            f"\n"
            f"  Session    : {self._session_id}\n"
            f"  Device     : {self._settings.DEVICE_ID}\n"
            f"  Mode       : {self._settings.MONITORING_MODE.value}\n"
            f"  Server     : {self._settings.SERVER_URL}\n"
            f"  Platform   : {platform.system()} {platform.release()}\n"
            f"  Started    : {now}\n"
            f"\n"
            f"  Press Ctrl+C to stop.\n"
        )

    def _register_signal_handlers(self) -> None:
        """Register OS signal handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_signal, sig)
            except (NotImplementedError, AttributeError):
                # Windows does not support add_signal_handler
                # Ctrl+C will raise KeyboardInterrupt instead
                pass

    def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        logger.info("Received signal %s - initiating shutdown", sig.name)
        self._shutdown_event.set()

    async def start(self) -> None:
        """Start the agent and run until shutdown is requested."""
        self._running = True
        self._display_startup_banner()

        logger.info(
            "Agent started - device=%s mode=%s session=%s",
            self._settings.DEVICE_ID,
            self._settings.MONITORING_MODE.value,
            self._session_id,
        )

        self._register_signal_handlers()

        # Future phases will start monitoring, transport, etc. here.

        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass

        await self.stop()

    async def stop(self) -> None:
        """Perform graceful shutdown."""
        if not self._running:
            return

        logger.info("Shutting down agent - session=%s", self._session_id)

        # Future phases will stop monitoring, flush events, etc. here.

        self._running = False
        logger.info("Agent shutdown complete")
