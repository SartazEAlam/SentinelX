"""Classification result and evidence models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SensitivityLevel(StrEnum):
    """Data sensitivity classification levels."""

    UNKNOWN = "UNKNOWN"
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL"
    CRITICAL = "CRITICAL"


class Evidence(BaseModel):
    """Structured evidence found during classification."""

    source: str
    rule: str
    category: str
    confidence: float
    location: str | None = None
    redacted_value: str | None = None
    description: str | None = None


class ClassificationResult(BaseModel):
    """The result of a data sensitivity classification operation."""

    sensitivity_level: SensitivityLevel
    confidence: float
    categories: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    content_inspected: bool = False
    inspection_complete: bool = False

    classifier_version: str = "3.0.0"
    model_name: str | None = None
    model_version: str | None = None
    classified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to the backend API expected dict format."""
        return {
            "sensitivity_level": self.sensitivity_level.value,
            "confidence": self.confidence,
            "categories": self.categories,
            "evidence": [e.model_dump() for e in self.evidence],
            "content_inspected": self.content_inspected,
            "inspection_complete": self.inspection_complete,
            "classifier_version": self.classifier_version,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "classified_at": self.classified_at.isoformat(),
        }
