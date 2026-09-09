"""Risk assessment engine.

Future implementations:
    - RiskAssessor: multi-factor risk scoring
    - RiskScore: risk level with contributing factors
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseRiskAssessor(ABC):
    """Abstract base for risk assessment."""

    @abstractmethod
    def assess(self, event: dict[str, Any]) -> float:
        """Assess the risk score for a security event.

        Args:
            event: Event data dictionary.

        Returns:
            Risk score between 0.0 (no risk) and 1.0 (critical risk).
        """
        ...
