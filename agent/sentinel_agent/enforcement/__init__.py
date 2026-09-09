"""Enforcement action execution.

Future implementations:
    - EnforcementEngine: execute policy decisions (block, warn, etc.)
    - FileBlocker: prevent file copy/move operations
    - USBController: USB device access control
"""

from abc import ABC, abstractmethod

from sentinel_agent.policy import PolicyAction


class BaseEnforcer(ABC):
    """Abstract base for enforcement actions."""

    @abstractmethod
    async def enforce(self, action: PolicyAction, context: dict) -> bool:
        """Execute an enforcement action.

        Args:
            action: The policy action to enforce.
            context: Event context information.

        Returns:
            True if enforcement was successful.
        """
        ...
