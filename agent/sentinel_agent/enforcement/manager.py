"""Top-level Enforcement Manager — integrates Phase 5 into the agent.

Provides the single entry point for the agent pipeline to evaluate
and enforce protected operations. Runs background polling for approvals.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sentinel_agent.enforcement.allow_handler import AllowHandler
from sentinel_agent.enforcement.backend_client import EnforcementBackendClient
from sentinel_agent.enforcement.block_handler import BlockHandler
from sentinel_agent.enforcement.destination_detector import DestinationDetector
from sentinel_agent.enforcement.hold_handler import HoldHandler
from sentinel_agent.enforcement.models import EnforcementResult
from sentinel_agent.enforcement.operation_controller import OperationController
from sentinel_agent.enforcement.rollback import RollbackManager
from sentinel_agent.enforcement.staging import StagingManager
from sentinel_agent.enforcement.transfer_enforcer import ExternalTransferEnforcer
from sentinel_agent.enforcement.usb_enforcer import USBEnforcer
from sentinel_agent.pipeline.models import EndpointEvent
from sentinel_agent.transport.http_transport import HTTPTransport

logger = logging.getLogger(__name__)


class EnforcementManager:
    """Manages the Phase 5 Enforcement & Prevention subsystem.

    Integrates the controllers, handlers, staging, and backend clients.
    Runs a background task to poll for approvals and clean up expired staging.
    """

    def __init__(
        self,
        transport: HTTPTransport,
        base_dir: Path,
        trusted_paths: list[Path] | None = None,
        max_staging_mb: int = 500,
        approval_timeout: int = 300,
        offline_policy_high: str = "BLOCK",
    ) -> None:
        self._running = False
        self._task: asyncio.Task[None] | None = None

        # 1. Staging & Safety
        self.staging_dir = base_dir / "staging"
        self._staging = StagingManager(
            staging_dir=self.staging_dir,
            max_total_size_mb=max_staging_mb,
            default_expiry_seconds=approval_timeout,
        )
        self._rollback = RollbackManager(self._staging)

        # 2. Handlers
        self._allow = AllowHandler()
        self._hold = HoldHandler(self._staging)
        self._block = BlockHandler()

        # 3. Controller
        self._controller = OperationController(
            allow_handler=self._allow,
            hold_handler=self._hold,
            block_handler=self._block,
            rollback_manager=self._rollback,
            approval_timeout_seconds=approval_timeout,
        )

        # 4. Environment / Detection
        self._detector = DestinationDetector(trusted_paths=trusted_paths)
        self.usb = USBEnforcer(self._detector)
        self.transfer = ExternalTransferEnforcer(self._detector)

        # 5. Backend integration
        self._client = EnforcementBackendClient(
            transport=transport,
            offline_policy_high=offline_policy_high,
        )

        # Local offline queue for results
        self._result_queue: list[dict] = []
        self._max_queue = 1000

    async def start(self) -> None:
        """Start the enforcement background tasks (polling & cleanup)."""
        if self._running:
            return
        self._running = True

        # Clean up any orphaned staging files on startup
        cleaned = self._staging.cleanup_all()
        if cleaned > 0:
            logger.info("Enforcement startup: cleaned %d orphaned staging files", cleaned)

        self._task = asyncio.create_task(self._background_loop())
        logger.info("Enforcement Manager started")

    async def stop(self) -> None:
        """Stop background tasks and clean up."""
        if not self._running:
            return
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        # Emergency cleanup on shutdown
        self._staging.cleanup_all()
        logger.info("Enforcement Manager stopped")

    async def evaluate_and_enforce(
        self,
        event: EndpointEvent,
        controlled: bool = False,
    ) -> EnforcementResult | None:
        """Process an event through the enforcement pipeline.

        Args:
            event: The normalized security event.
            controlled: True if this is a pre-evaluation controlled transfer
                       where SentinelX prevents the operation. False if passive.

        Returns:
            The EnforcementResult, or None if the event type isn't enforced.
        """
        # We only enforce COPY/MOVE/UPLOAD operations
        if event.action not in ("file_copy", "file_move", "file_upload") and event.event_type not in ("FILE_COPY", "FILE_MOVE", "FILE_UPLOAD", "NETWORK_TRANSFER"):
            return None

        # 1. Get decision from server
        decision = await self._client.evaluate_operation(event)

        # 2. Execute enforcement
        result = self._controller.execute_decision(
            decision=decision,
            source_path=event.file_path or event.source,
            destination=event.destination,
            source_hash=event.file_hash or "",
            file_size=event.file_size or 0,
            file_name=event.file_name,
            controlled=controlled,
        )

        # 3. Report result (async fire-and-forget or queue)
        await self._queue_result(result)

        return result

    async def _queue_result(self, result: EnforcementResult) -> None:
        """Queue and attempt to send the result to the server."""
        r_dict = result.to_api_dict()

        if len(self._result_queue) < self._max_queue:
            self._result_queue.append(r_dict)

        # We will let the background loop drain the queue

    async def _background_loop(self) -> None:
        """Background loop for polling approvals, cleanup, and result sending."""
        poll_interval = 2.0
        cleanup_counter = 0

        while self._running:
            try:
                await asyncio.sleep(poll_interval)

                # 1. Send queued results
                await self._drain_results()

                # 2. Check pending approvals
                await self._poll_approvals()

                # 3. Cleanup expired holds (every ~10 seconds)
                cleanup_counter += 1
                if cleanup_counter >= 5:
                    self._cleanup_expired()
                    cleanup_counter = 0

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Enforcement background loop error: %s", exc)

    async def _drain_results(self) -> None:
        """Attempt to send all queued results."""
        if not self._result_queue:
            return

        failed = []
        for r_dict in self._result_queue:
            success = await self._client.submit_result(r_dict)
            if not success:
                failed.append(r_dict)

        self._result_queue = failed

    async def _poll_approvals(self) -> None:
        """Check the server for updates on pending HOLD operations."""
        pending_ops = self._controller.get_pending_approvals()

        for op_id in pending_ops:
            op = self._controller.get_operation(op_id)
            if not op:
                continue

            status_data = await self._client.check_approval_status(op_id, op.event_id)
            status = status_data.get("status")

            if status == "APPROVED":
                result = self._controller.handle_approval_response(
                    operation_id=op_id,
                    approved=True,
                    approval_id=status_data.get("approval_id", ""),
                    reason=status_data.get("reason", ""),
                )
                await self._queue_result(result)
                self._controller.cleanup_operation(op_id)

            elif status == "REJECTED":
                result = self._controller.handle_approval_response(
                    operation_id=op_id,
                    approved=False,
                    approval_id=status_data.get("approval_id", ""),
                    reason=status_data.get("reason", ""),
                )
                await self._queue_result(result)
                self._controller.cleanup_operation(op_id)

    def _cleanup_expired(self) -> None:
        """Handle locally expired holds."""
        expired_ops = self._rollback.cleanup_expired_operations()
        for op_id in expired_ops:
            result = self._controller.handle_expiration(op_id)
            # Create a fire-and-forget task to queue the result
            asyncio.create_task(self._queue_result(result))
            self._controller.cleanup_operation(op_id)
