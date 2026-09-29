"""Enforcement state machine — explicit operation lifecycle states and transitions.

Every enforcement operation follows a deterministic state machine.
Invalid transitions are rejected, and every transition is recorded.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import StrEnum

from sentinel_agent.enforcement.errors import InvalidStateTransitionError

logger = logging.getLogger(__name__)


class OperationState(StrEnum):
    """Enforcement operation lifecycle states."""

    # Initial detection
    DETECTED = "DETECTED"
    EVALUATING = "EVALUATING"

    # ALLOW path
    ALLOW_PENDING_EXECUTION = "ALLOW_PENDING_EXECUTION"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"

    # HOLD path
    HOLD_PENDING = "HOLD_PENDING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"

    # BLOCK path
    BLOCK_PENDING = "BLOCK_PENDING"
    BLOCKED = "BLOCKED"

    # Failure / cleanup
    FAILED = "FAILED"
    CLEANUP_REQUIRED = "CLEANUP_REQUIRED"
    CLEANED = "CLEANED"


# ── Valid transitions ────────────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[OperationState, set[OperationState]] = {
    OperationState.DETECTED: {OperationState.EVALUATING},
    OperationState.EVALUATING: {
        OperationState.ALLOW_PENDING_EXECUTION,
        OperationState.HOLD_PENDING,
        OperationState.BLOCK_PENDING,
        OperationState.FAILED,
    },

    # ALLOW path
    OperationState.ALLOW_PENDING_EXECUTION: {
        OperationState.EXECUTING,
        OperationState.FAILED,
    },
    OperationState.EXECUTING: {
        OperationState.COMPLETED,
        OperationState.FAILED,
    },

    # HOLD path
    OperationState.HOLD_PENDING: {
        OperationState.WAITING_APPROVAL,
        OperationState.FAILED,
        OperationState.BLOCKED,  # staging failure → block
    },
    OperationState.WAITING_APPROVAL: {
        OperationState.APPROVED,
        OperationState.DENIED,
        OperationState.EXPIRED,
        OperationState.FAILED,
    },
    OperationState.APPROVED: {
        OperationState.EXECUTING,
        OperationState.FAILED,
    },
    OperationState.DENIED: {
        OperationState.CLEANUP_REQUIRED,
        OperationState.CLEANED,
    },
    OperationState.EXPIRED: {
        OperationState.CLEANUP_REQUIRED,
        OperationState.CLEANED,
        OperationState.BLOCKED,
    },

    # BLOCK path
    OperationState.BLOCK_PENDING: {
        OperationState.BLOCKED,
        OperationState.CLEANUP_REQUIRED,
    },
    OperationState.BLOCKED: {
        OperationState.CLEANUP_REQUIRED,
        OperationState.CLEANED,
    },

    # Terminal / cleanup
    OperationState.COMPLETED: set(),  # terminal
    OperationState.FAILED: {
        OperationState.CLEANUP_REQUIRED,
        OperationState.CLEANED,
    },
    OperationState.CLEANUP_REQUIRED: {
        OperationState.CLEANED,
        OperationState.FAILED,
    },
    OperationState.CLEANED: set(),  # terminal
}


class StateTransition:
    """Record of a single state transition."""

    __slots__ = ("from_state", "to_state", "timestamp", "reason")

    def __init__(
        self,
        from_state: OperationState,
        to_state: OperationState,
        reason: str = "",
    ) -> None:
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = datetime.now(UTC)
        self.reason = reason

    def to_dict(self) -> dict:
        return {
            "from": self.from_state.value,
            "to": self.to_state.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
        }


class OperationStateMachine:
    """Manages the state of a single enforcement operation.

    Validates transitions and records full history.
    """

    def __init__(self, operation_id: str) -> None:
        self._operation_id = operation_id
        self._state = OperationState.DETECTED
        self._history: list[StateTransition] = []
        self._created_at = datetime.now(UTC)

    @property
    def state(self) -> OperationState:
        return self._state

    @property
    def operation_id(self) -> str:
        return self._operation_id

    @property
    def history(self) -> list[StateTransition]:
        return list(self._history)

    @property
    def is_terminal(self) -> bool:
        """Check if the operation is in a terminal state."""
        return self._state in (
            OperationState.COMPLETED,
            OperationState.CLEANED,
        )

    @property
    def is_active(self) -> bool:
        """Check if the operation still requires processing."""
        return not self.is_terminal and self._state != OperationState.BLOCKED

    def can_transition_to(self, new_state: OperationState) -> bool:
        """Check if the transition is valid without performing it."""
        allowed = _VALID_TRANSITIONS.get(self._state, set())
        return new_state in allowed

    def transition(self, new_state: OperationState, reason: str = "") -> None:
        """Perform a validated state transition.

        Raises:
            InvalidStateTransitionError: If the transition is not allowed.
        """
        if not self.can_transition_to(new_state):
            raise InvalidStateTransitionError(
                f"Invalid transition: {self._state} → {new_state} "
                f"(operation={self._operation_id})",
                operation_id=self._operation_id,
            )

        transition = StateTransition(self._state, new_state, reason)
        self._history.append(transition)

        logger.info(
            "Operation %s: %s → %s%s",
            self._operation_id[:12],
            self._state.value,
            new_state.value,
            f" ({reason})" if reason else "",
        )
        self._state = new_state

    def force_state(self, new_state: OperationState, reason: str = "") -> None:
        """Force a state without validation (crash recovery only)."""
        transition = StateTransition(self._state, new_state, reason)
        self._history.append(transition)
        logger.warning(
            "Operation %s: FORCED %s → %s (%s)",
            self._operation_id[:12],
            self._state.value,
            new_state.value,
            reason,
        )
        self._state = new_state
