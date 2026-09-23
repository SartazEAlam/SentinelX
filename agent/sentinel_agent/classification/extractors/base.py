"""Base extractor interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Extractor(ABC):
    """Abstract base class for all file content extractors."""

    @abstractmethod
    def extract(self, path: Path) -> dict[str, Any]:
        """Extract context from a file safely.

        Args:
            path: Path to the file.

        Returns:
            A dictionary containing extraction results (e.g., 'text', 'headers').
            If extraction fails or is unsupported, it returns an empty dict or partial result.
        """
        ...
