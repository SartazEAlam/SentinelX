"""Base rule engine interface."""

from abc import ABC, abstractmethod
from typing import Any

from sentinel_agent.classification.result import Evidence


class ClassificationRule(ABC):
    """Abstract base class for all classification rules."""

    def __init__(self, name: str, category: str, confidence: float, evidence_desc: str):
        self.name = name
        self.category = category
        self.confidence = confidence
        self.evidence_desc = evidence_desc

    @abstractmethod
    def evaluate(self, context: dict[str, Any]) -> list[Evidence]:
        """Evaluate the rule against the provided context.
        
        Args:
            context: Dictionary containing 'filename', 'extension', 'text', 'headers', etc.
            
        Returns:
            A list of Evidence objects found by this rule.
        """
        ...
