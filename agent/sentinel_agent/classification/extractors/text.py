"""Safe text extractor for common formats."""

import logging
from pathlib import Path
from typing import Any

from sentinel_agent.classification.extractors.base import Extractor

logger = logging.getLogger(__name__)


class TextExtractor(Extractor):
    """Extracts raw text from common text-based files, with strict limits.

    Supported files: .txt, .md, .json, source code.
    """

    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".xml",
        ".log",
        ".py",
        ".js",
        ".ts",
        ".java",
        ".cpp",
        ".c",
        ".go",
        ".rs",
        ".sql",
        ".env",
    }

    def __init__(self, max_bytes: int = 10 * 1024 * 1024):  # 10MB default
        self.max_bytes = max_bytes

    def extract(self, path: Path) -> dict[str, Any]:
        context: dict[str, Any] = {
            "text": "",
            "inspected": False,
            "complete": False,
            "reason": None,
        }

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            context["reason"] = "UNSUPPORTED_EXTENSION"
            return context

        try:
            stat = path.stat()
            file_size = stat.st_size

            if file_size == 0:
                context["reason"] = "EMPTY_FILE"
                context["inspected"] = True
                context["complete"] = True
                return context

            # Only read up to max_bytes
            read_size = min(file_size, self.max_bytes)

            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read(read_size)

            context["text"] = text
            context["inspected"] = True

            if file_size > self.max_bytes:
                context["complete"] = False
                context["reason"] = "SIZE_LIMIT"
            else:
                context["complete"] = True

        except (OSError, PermissionError) as exc:
            logger.debug("Failed to extract text from %s: %s", path, exc)
            context["reason"] = "ACCESS_ERROR"
        except Exception as exc:
            logger.debug("Unexpected error extracting text from %s: %s", path, exc)
            context["reason"] = "EXTRACTION_ERROR"

        return context
