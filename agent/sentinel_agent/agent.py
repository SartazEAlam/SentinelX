"""SentinelX Endpoint Agent — core lifecycle management."""

import asyncio
import logging
import platform
import signal
from datetime import UTC, datetime
from enum import StrEnum

from sentinel_agent import __version__
from sentinel_agent.config import AgentSettings
from sentinel_agent.identity import DeviceIdentity, IdentityManager
from sentinel_agent.monitoring.filesystem import FileSystemCollector
from sentinel_agent.monitoring.usb import USBCollector
from sentinel_agent.pipeline.deduplicator import EventDeduplicator
from sentinel_agent.pipeline.dispatcher import EventDispatcher
from sentinel_agent.pipeline.normalizer import EventNormalizer
from sentinel_agent.pipeline.queue import EventQueue
from sentinel_agent.classification.engine import ClassificationEngine
from sentinel_agent.storage.event_store import LocalEventStore
from sentinel_agent.transport.http_transport import HTTPTransport

logger = logging.getLogger(__name__)


class AgentState(StrEnum):
    """Agent lifecycle states."""

    INITIALIZING = "INITIALIZING"
    REGISTERING = "REGISTERING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class SentinelAgent:
    """Core SentinelX endpoint agent.

    Manages the full agent lifecycle: identity, registration, monitoring,
    event pipeline, heartbeat, and graceful shutdown.
    """

    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings
        self._state = AgentState.STOPPED
        self._shutdown_event = asyncio.Event()

        # Components (initialised during start)
        self._identity_mgr: IdentityManager | None = None
        self._identity: DeviceIdentity | None = None
        self._transport: HTTPTransport | None = None
        self._store: LocalEventStore | None = None
        self._queue: EventQueue | None = None
        self._normalizer: EventNormalizer | None = None
        self._dedup: EventDeduplicator | None = None
        self._dispatcher: EventDispatcher | None = None
        self._fs_collector: FileSystemCollector | None = None
        self._usb_collector: USBCollector | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None

    @property
    def device_id(self) -> str:
        """Return the device identifier."""
        if self._identity is not None:
            return self._identity.device_id
        return self._settings.DEVICE_ID

    @property
    def is_running(self) -> bool:
        """Check whether the agent is currently running."""
        return self._state in (AgentState.RUNNING, AgentState.DEGRADED)

    @property
    def state(self) -> AgentState:
        """Current agent state."""
        return self._state

    def _set_state(self, new_state: AgentState) -> None:
        """Transition to a new state with logging."""
        old_state = self._state
        self._state = new_state
        logger.info("Agent state: %s → %s", old_state, new_state)

    def _display_startup_banner(self) -> None:
        """Print agent startup information to the console."""
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        device = self._identity.device_id if self._identity else self._settings.DEVICE_ID
        print(
            f"\n"
            f"  +------------------------------------------+\n"
            f"  |         SentinelX Endpoint Agent         |\n"
            f"  |              v{__version__:<16}      |\n"
            f"  +------------------------------------------+\n"
            f"\n"
            f"  Device     : {device}\n"
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
                pass

    def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        logger.info("Received signal %s — initiating shutdown", sig.name)
        self._shutdown_event.set()

    # ── Lifecycle ───────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the agent and run until shutdown is requested."""
        self._set_state(AgentState.INITIALIZING)
        self._display_startup_banner()
        self._register_signal_handlers()

        try:
            # 1. Identity
            self._identity_mgr = IdentityManager(self._settings.identity_path)
            self._identity = self._identity_mgr.load()

            # 2. Transport
            self._transport = HTTPTransport(
                server_url=self._settings.SERVER_URL,
                token=self._identity.token if self._identity.is_registered else "",
                max_retries=self._settings.MAX_RETRY_ATTEMPTS,
                backoff_seconds=self._settings.RETRY_BACKOFF_SECONDS,
            )

            # 3. Register if needed
            if not self._identity.is_registered:
                await self._register_with_backend()

            # 4. Local event store
            store_path = self._settings.identity_path / "event_store.db"
            self._store = LocalEventStore(store_path)
            await self._store.init_db()

            # 5. Pipeline
            self._queue = EventQueue()
            
            # Classification
            config_path = self._settings.base_dir / "classification_rules.json"
            classification_engine = ClassificationEngine(
                config_path=config_path, 
                ml_dir=self._settings.base_dir / "models" if (self._settings.base_dir / "models").exists() else None
            )
            
            self._normalizer = EventNormalizer(
                hash_enabled=self._settings.FILE_HASH_ENABLED,
                hash_max_bytes=self._settings.file_hash_max_bytes,
                classification_engine=classification_engine
            )
            self._dedup = EventDeduplicator()

            # 6. Dispatcher
            self._dispatcher = EventDispatcher(
                queue=self._queue,
                transport=self._transport,
                store=self._store,
                batch_size=self._settings.BATCH_SIZE,
                flush_interval=self._settings.BATCH_FLUSH_INTERVAL_SECONDS,
            )
            await self._dispatcher.start()

            # 7. Filesystem collector
            paths = self._settings.protected_path_list
            if paths:
                self._fs_collector = FileSystemCollector(
                    paths=paths,
                    event_queue=self._queue,
                    normalizer=self._normalizer,
                    deduplicator=self._dedup,
                    excluded_extensions=self._settings.excluded_extension_set,
                    excluded_directories=self._settings.excluded_directory_set,
                )
                await self._fs_collector.start()

            # 8. USB collector
            self._usb_collector = USBCollector(
                event_queue=self._queue,
                normalizer=self._normalizer,
                poll_interval=self._settings.USB_POLL_INTERVAL_SECONDS,
            )
            await self._usb_collector.start()

            # 9. Heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self._set_state(AgentState.RUNNING)
            logger.info("Agent fully operational — monitoring active")

        except Exception as exc:
            logger.error("Failed to start agent: %s", exc)
            self._set_state(AgentState.DEGRADED)

        # Wait for shutdown
        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass

        await self.stop()

    async def stop(self) -> None:
        """Perform graceful shutdown."""
        if self._state == AgentState.STOPPED:
            return

        self._set_state(AgentState.STOPPING)

        # Stop heartbeat
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        # Stop collectors
        if self._fs_collector is not None:
            await self._fs_collector.stop()
        if self._usb_collector is not None:
            await self._usb_collector.stop()

        # Stop dispatcher (flushes remaining events)
        if self._dispatcher is not None:
            await self._dispatcher.stop()

        # Close transport
        if self._transport is not None:
            await self._transport.close()

        # Close local store
        if self._store is not None:
            await self._store.close()

        self._set_state(AgentState.STOPPED)
        logger.info("Agent shutdown complete")

    # ── Registration ────────────────────────────────────────────────

    async def _register_with_backend(self) -> None:
        """Register the device with the SentinelX backend."""
        if self._transport is None or self._identity is None or self._identity_mgr is None:
            raise RuntimeError("Transport and identity must be initialised before registration")

        self._set_state(AgentState.REGISTERING)

        registration_data = {
            "device_id": self._identity.device_id,
            "device_name": self._identity.device_name,
            "hostname": self._identity.hostname,
            "operating_system": self._identity.operating_system,
            "os_version": self._identity.os_version,
            "agent_version": self._identity.agent_version,
        }

        result = await self._transport.register_device(registration_data)

        if result.success and result.data:
            token = result.data.get("token", "")
            if token:
                self._identity_mgr.set_token(token)
                self._transport.set_token(token)
                logger.info("Device registered successfully: %s", self._identity.device_id)
            else:
                logger.error("Registration succeeded but no token returned")
        else:
            logger.error("Device registration failed: %s", result.error)
            logger.warning("Agent will run in degraded mode — events stored locally")

    # ── Heartbeat ───────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to the backend."""
        while True:
            try:
                await asyncio.sleep(self._settings.HEARTBEAT_INTERVAL_SECONDS)
                await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Heartbeat error: %s", exc)

    async def _send_heartbeat(self) -> None:
        """Send a single heartbeat."""
        if self._transport is None:
            return

        heartbeat_data = {
            "agent_version": __version__,
        }

        result = await self._transport.send_heartbeat(heartbeat_data)
        if result.success:
            logger.debug("Heartbeat sent successfully")
            if self._state == AgentState.DEGRADED:
                self._set_state(AgentState.RUNNING)
        else:
            logger.warning("Heartbeat failed: %s", result.error)
            if self._state == AgentState.RUNNING:
                self._set_state(AgentState.DEGRADED)
