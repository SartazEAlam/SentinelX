"""Safe CSV extractor."""

import csv
import logging
from pathlib import Path
from typing import Any

from sentinel_agent.classification.extractors.base import Extractor

logger = logging.getLogger(__name__)


class CSVExtractor(Extractor):
    """Extracts headers and limited text from CSV files safely."""

    def __init__(self, max_rows: int = 100):
        self.max_rows = max_rows

    def extract(self, path: Path) -> dict[str, Any]:
        context: dict[str, Any] = {
            "headers": [],
            "text": "",
            "inspected": False,
            "complete": False,
            "reason": None,
        }

        if path.suffix.lower() != ".csv":
            context["reason"] = "NOT_CSV"
            return context

        try:
            # We don't read huge CSVs into memory, we just stream the first N rows
            with open(path, encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)

                rows_read = 0
                sample_text = []

                for row in reader:
                    if rows_read == 0:
                        context["headers"] = row

                    sample_text.append(",".join(row))
                    rows_read += 1

                    if rows_read >= self.max_rows:
                        break

                context["text"] = "\n".join(sample_text)
                context["inspected"] = True

                # Check if we didn't read the whole file
                # A robust way would be to check f.tell() vs file size, but this is an approximation
                if rows_read >= self.max_rows:
                    context["complete"] = False
                    context["reason"] = "MAX_ROWS_REACHED"
                else:
                    context["complete"] = True

        except (OSError, PermissionError) as exc:
            logger.debug("Failed to extract CSV from %s: %s", path, exc)
            context["reason"] = "ACCESS_ERROR"
        except Exception as exc:
            logger.debug("Unexpected error extracting CSV from %s: %s", path, exc)
            context["reason"] = "EXTRACTION_ERROR"

        return context
