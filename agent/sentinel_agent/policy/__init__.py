"""Policy evaluation engine.

Future implementations:
    - PolicyEngine: evaluate events against configured policies
    - PolicyAction enum: ALLOW, LOG, WARN, BLOCK, REQUIRE_APPROVAL
"""

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any


class PolicyAction(StrEnum):
    """Actions that can result from policy evaluation."""

    ALLOW = "ALLOW"
    LOG = "LOG"
    WARN = "WARN"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class BasePolicyEngine(ABC):
    """Abstract base for policy evaluation."""

    @abstractmethod
    def evaluate(self, event: dict[str, Any]) -> PolicyAction:
        """Evaluate an event against active policies.

        Args:
            event: Event data dictionary.

        Returns:
            The determined policy action.
        """
        ...
