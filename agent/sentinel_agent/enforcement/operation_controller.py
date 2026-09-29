"""Operation controller — orchestrates the full enforcement lifecycle.

Receives a detected operation, drives it through the state machine,
dispatches to the correct handler (ALLOW/HOLD/BLOCK), and produces
an EnforcementResult.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from sentinel_agent.enforcement.allow_handler import AllowHandler
from sentinel_agent.enforcement.block_handler import BlockHandler
from sentinel_agent.enforcement.errors import (
    EnforcementError,
    EnforcementErrorCode,
    InvalidStateTransitionError,
)
from sentinel_agent.enforcement.hold_handler import HoldHandler
from sentinel_agent.enforcement.models import (
    Decision,
    EnforcementDecision,
    EnforcementOperation,
    EnforcementResult,
    EnforcementStatus,
)
from sentinel_agent.enforcement.rollback import RollbackManager
from sentinel_agent.enforcement.state_machine import OperationState, OperationStateMachine

logger = logging.getLogger(__name__)


class OperationController:
    """Central orchestrator for enforcement operations.

    Manages the full lifecycle: detection → evaluation → enforcement → result.
    Tracks active operations and handles concurrency via operation IDs.
    """

    def __init__(
        self,
        allow_handler: AllowHandler,
        hold_handler: HoldHandler,
        block_handler: BlockHandler,
        rollback_manager: RollbackManager,
        approval_timeout_seconds: int = 300,
        operation_timeout_seconds: int = 60,
    ) -> None:
        self._allow = allow_handler
        self._hold = hold_handler
        self._block = block_handler
        self._rollback = rollback_manager
        self._approval_timeout = approval_timeout_seconds
        self._operation_timeout = operation_timeout_seconds

        # Active operations tracked by operation_id
        self._operations: dict[str, EnforcementOperation] = {}
        self._state_machines: dict[str, OperationStateMachine] = {}

        # Metrics
        self.total_operations: int = 0
        self.allowed_count: int = 0
        self.held_count: int = 0
        self.blocked_count: int = 0
        self.approved_count: int = 0
        self.denied_count: int = 0
        self.expired_count: int = 0
        self.failed_count: int = 0

    @property
    def active_operations(self) -> dict[str, EnforcementOperation]:
        return dict(self._operations)

    def get_operation(self, operation_id: str) -> EnforcementOperation | None:
        return self._operations.get(operation_id)

    def get_state(self, operation_id: str) -> OperationState | None:
        sm = self._state_machines.get(operation_id)
        return sm.state if sm else None

    def execute_decision(
        self,
        decision: EnforcementDecision,
        source_path: str,
        destination: str,
        source_hash: str = "",
        file_size: int = 0,
        file_name: str = "",
        controlled: bool = False,
    ) -> EnforcementResult:
        """Execute an enforcement decision through the full lifecycle.

        Args:
            decision: The EnforcementDecision from the server.
            source_path: Path to the source file.
            destination: Target destination.
            source_hash: Pre-computed source hash.
            file_size: Size of the source file.
            file_name: Name of the file.
            controlled: True for SentinelX-controlled transfers.

        Returns:
            EnforcementResult with the final outcome.
        """
        # Validate decision
        if decision.is_expired():
            logger.warning(
                "Decision %s expired — treating as BLOCK",
                decision.decision_id[:12],
            )
            decision.decision = Decision.BLOCK

        # Create operation tracking
        operation = EnforcementOperation(
            event_id=decision.event_id,
            decision=decision.decision,
            source_path=source_path,
            source_hash=source_hash,
            file_name=file_name or Path(source_path).name,
            file_size=file_size,
            destination=destination,
            risk_assessment_id=decision.risk_assessment_id,
            risk_score=decision.risk_score,
            risk_level=decision.risk_level,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
        )

        sm = OperationStateMachine(operation.operation_id)

        self._operations[operation.operation_id] = operation
        self._state_machines[operation.operation_id] = sm
        self.total_operations += 1

        try:
            # DETECTED → EVALUATING
            sm.transition(OperationState.EVALUATING, "Decision received from server")
            operation.started_at = datetime.now(UTC)

            # Dispatch to appropriate handler
            if decision.decision == Decision.ALLOW:
                return self._handle_allow(operation, sm, controlled)
            elif decision.decision == Decision.HOLD:
                return self._handle_hold(operation, sm, controlled)
            elif decision.decision == Decision.BLOCK:
                return self._handle_block(operation, sm, controlled)
            else:
                # Unknown decision → fail closed
                logger.error("Unknown decision: %s — treating as BLOCK", decision.decision)
                return self._handle_block(operation, sm, controlled)

        except InvalidStateTransitionError as exc:
            logger.error("State transition error: %s", exc.message)
            self.failed_count += 1
            operation.error_code = exc.code.value
            operation.error_message = exc.message
            return EnforcementResult(
                operation_id=operation.operation_id,
                status=EnforcementStatus.FAILED,
                decision=decision.decision,
                error_code=exc.code.value,
                message=exc.message,
            )
        except EnforcementError as exc:
            logger.error("Enforcement error: %s", exc.message)
            self.failed_count += 1
            operation.error_code = exc.code.value
            operation.error_message = exc.message
            self._safe_transition(sm, OperationState.FAILED, exc.message)
            return EnforcementResult(
                operation_id=operation.operation_id,
                status=EnforcementStatus.FAILED,
                decision=decision.decision,
                error_code=exc.code.value,
                message=exc.message,
            )
        except Exception as exc:
            logger.error("Unexpected enforcement error: %s", exc, exc_info=True)
            self.failed_count += 1
            self._safe_transition(sm, OperationState.FAILED, str(exc))
            return EnforcementResult(
                operation_id=operation.operation_id,
                status=EnforcementStatus.FAILED,
                decision=decision.decision,
                error_code="UNEXPECTED_ERROR",
                message=str(exc),
            )

    def _handle_allow(
        self,
        operation: EnforcementOperation,
        sm: OperationStateMachine,
        controlled: bool,
    ) -> EnforcementResult:
        """Process an ALLOW decision."""
        sm.transition(OperationState.ALLOW_PENDING_EXECUTION, "ALLOW decision")

        if controlled:
            sm.transition(OperationState.EXECUTING, "Starting controlled transfer")

        result = self._allow.handle(
            operation_id=operation.operation_id,
            source_path=operation.source_path,
            destination=operation.destination,
            source_hash=operation.source_hash,
            controlled=controlled,
        )

        if result.status in (EnforcementStatus.ALLOWED, EnforcementStatus.COMPLETED):
            sm.transition(OperationState.COMPLETED, "Transfer completed")
            self.allowed_count += 1
        else:
            sm.transition(OperationState.FAILED, result.message)
            self.failed_count += 1

        operation.completed_at = datetime.now(UTC)
        operation.destination_hash = result.destination_hash
        operation.bytes_transferred = result.bytes_transferred
        return result

    def _handle_hold(
        self,
        operation: EnforcementOperation,
        sm: OperationStateMachine,
        controlled: bool,
    ) -> EnforcementResult:
        """Process a HOLD decision — stage and wait for approval."""
        sm.transition(OperationState.HOLD_PENDING, "HOLD decision")

        result = self._hold.hold(
            operation_id=operation.operation_id,
            event_id=operation.event_id,
            source_path=operation.source_path,
            destination=operation.destination,
            source_hash=operation.source_hash,
            approval_timeout_seconds=self._approval_timeout,
        )

        if result.status == EnforcementStatus.HELD:
            sm.transition(OperationState.WAITING_APPROVAL, "File staged, awaiting approval")
            self.held_count += 1
        else:
            sm.transition(OperationState.FAILED, result.message)
            self.failed_count += 1

        return result

    def _handle_block(
        self,
        operation: EnforcementOperation,
        sm: OperationStateMachine,
        controlled: bool,
    ) -> EnforcementResult:
        """Process a BLOCK decision — prevent the transfer."""
        sm.transition(OperationState.BLOCK_PENDING, "BLOCK decision")

        result = self._block.handle(
            operation_id=operation.operation_id,
            source_path=operation.source_path,
            destination=operation.destination,
            source_hash=operation.source_hash,
            controlled=controlled,
            reason=f"Risk score: {operation.risk_score:.1f} ({operation.risk_level})",
        )

        sm.transition(OperationState.BLOCKED, "Transfer prevented")
        self.blocked_count += 1
        operation.completed_at = datetime.now(UTC)

        return result

    def handle_approval_response(
        self,
        operation_id: str,
        approved: bool,
        approval_id: str = "",
        reason: str = "",
    ) -> EnforcementResult:
        """Process an administrator's approval/denial response.

        Args:
            operation_id: The operation waiting for approval.
            approved: True = APPROVE, False = DENY.
            approval_id: Server-issued approval identifier.
            reason: Comment from the administrator.

        Returns:
            EnforcementResult with the final outcome.
        """
        sm = self._state_machines.get(operation_id)
        operation = self._operations.get(operation_id)

        if sm is None or operation is None:
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.HOLD,
                error_code=EnforcementErrorCode.OPERATION_NOT_FOUND,
                message="Operation not found",
            )

        if sm.state != OperationState.WAITING_APPROVAL:
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.HOLD,
                error_code=EnforcementErrorCode.INVALID_STATE_TRANSITION,
                message=f"Operation not waiting for approval (state={sm.state})",
            )

        if approved:
            sm.transition(OperationState.APPROVED, f"Approved by admin: {reason}")
            sm.transition(OperationState.EXECUTING, "Starting approved transfer")

            result = self._hold.approve(
                operation_id=operation_id,
                destination=operation.destination,
                approval_id=approval_id,
            )

            if result.status == EnforcementStatus.COMPLETED:
                sm.transition(OperationState.COMPLETED, "Approved transfer completed")
                self.approved_count += 1
            else:
                self._safe_transition(sm, OperationState.FAILED, result.message)
                self.failed_count += 1

            operation.approval_id = approval_id
            operation.completed_at = datetime.now(UTC)
            return result
        else:
            sm.transition(OperationState.DENIED, f"Denied by admin: {reason}")
            result = self._hold.deny(operation_id, reason)
            self.denied_count += 1

            self._safe_transition(sm, OperationState.CLEANED, "Staging cleaned after denial")
            operation.completed_at = datetime.now(UTC)
            return result

    def handle_expiration(self, operation_id: str) -> EnforcementResult:
        """Handle expiration of a held operation."""
        sm = self._state_machines.get(operation_id)
        operation = self._operations.get(operation_id)

        if sm is None or operation is None:
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.EXPIRED,
                decision=Decision.HOLD,
                message="Operation not found — treated as expired",
            )

        sm.transition(OperationState.EXPIRED, "Approval timeout")
        result = self._hold.expire(operation_id)
        self.expired_count += 1

        self._safe_transition(sm, OperationState.CLEANED, "Staging cleaned after expiration")
        operation.completed_at = datetime.now(UTC)
        return result

    def cleanup_operation(self, operation_id: str) -> None:
        """Remove a completed operation from active tracking."""
        self._operations.pop(operation_id, None)
        self._state_machines.pop(operation_id, None)

    def get_pending_approvals(self) -> list[str]:
        """Get operation IDs that are waiting for approval."""
        return [
            op_id
            for op_id, sm in self._state_machines.items()
            if sm.state == OperationState.WAITING_APPROVAL
        ]

    def get_metrics(self) -> dict[str, int]:
        """Get enforcement metrics."""
        return {
            "total_operations": self.total_operations,
            "allowed": self.allowed_count,
            "held": self.held_count,
            "blocked": self.blocked_count,
            "approved": self.approved_count,
            "denied": self.denied_count,
            "expired": self.expired_count,
            "failed": self.failed_count,
            "active": len(self._operations),
        }

    def _safe_transition(
        self,
        sm: OperationStateMachine,
        target: OperationState,
        reason: str,
    ) -> None:
        """Attempt a transition; log but don't raise on failure."""
        try:
            if sm.can_transition_to(target):
                sm.transition(target, reason)
        except InvalidStateTransitionError:
            logger.debug(
                "Could not transition %s to %s (current=%s)",
                sm.operation_id[:12],
                target.value,
                sm.state.value,
            )
