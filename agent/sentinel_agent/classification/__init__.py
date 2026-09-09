"""Data sensitivity classification.

Future implementations:
    - ContentClassifier: file content analysis (patterns, keywords)
    - MetadataClassifier: file metadata-based classification
    - SensitivityLevel enum: LOW, MEDIUM, HIGH, CRITICAL
"""

from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path


class SensitivityLevel(StrEnum):
    """Data sensitivity classification levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BaseClassifier(ABC):
    """Abstract base for data classifiers."""

    @abstractmethod
    def classify(self, file_path: Path) -> SensitivityLevel:
        """Classify the sensitivity level of a file.

        Args:
            file_path: Path to the file to classify.

        Returns:
            The determined sensitivity level.
        """
        ...
