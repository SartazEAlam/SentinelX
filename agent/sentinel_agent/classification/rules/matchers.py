"""Concrete classification rule implementations."""

import re
from typing import Any

from sentinel_agent.classification.result import Evidence
from sentinel_agent.classification.rules.base import ClassificationRule


class ExtensionRule(ClassificationRule):
    """Matches file extensions."""

    def __init__(self, ext: str, category: str, confidence: float, evidence_desc: str):
        super().__init__(f"ext_{ext}", category, confidence, evidence_desc)
        self.ext = ext.lower()

    def evaluate(self, context: dict[str, Any]) -> list[Evidence]:
        extension = context.get("extension", "").lower()
        if extension == self.ext:
            return [
                Evidence(
                    source="extension",
                    rule=self.name,
                    category=self.category,
                    confidence=self.confidence,
                    description=self.evidence_desc
                )
            ]
        return []


class FilenameRule(ClassificationRule):
    """Matches filename patterns."""

    def __init__(self, pattern: str, category: str, confidence: float, evidence_desc: str):
        super().__init__(f"filename_{pattern}", category, confidence, evidence_desc)
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def evaluate(self, context: dict[str, Any]) -> list[Evidence]:
        filename = context.get("filename", "")
        if self.pattern.match(filename):
            return [
                Evidence(
                    source="filename",
                    rule=self.name,
                    category=self.category,
                    confidence=self.confidence,
                    description=self.evidence_desc
                )
            ]
        return []


class KeywordRule(ClassificationRule):
    """Matches explicit keywords in extracted text."""

    def __init__(self, keyword: str, category: str, confidence: float, evidence_desc: str):
        super().__init__(f"keyword_{keyword}", category, confidence, evidence_desc)
        self.keyword = keyword.lower()
        # Word boundary to avoid partial matches
        self.pattern = re.compile(rf"\b{re.escape(self.keyword)}\b", re.IGNORECASE)

    def evaluate(self, context: dict[str, Any]) -> list[Evidence]:
        text = context.get("text", "")
        if not text:
            return []

        if self.pattern.search(text):
            return [
                Evidence(
                    source="keyword",
                    rule=self.name,
                    category=self.category,
                    confidence=self.confidence,
                    description=self.evidence_desc
                )
            ]
        return []


class RegexRule(ClassificationRule):
    """Matches regular expressions in text (e.g., emails, credit cards, API keys)."""

    def __init__(
        self, name: str, pattern: str, category: str, confidence: float, evidence_desc: str,
        redact: bool = True, redact_char: str = "*"
    ):
        super().__init__(name, category, confidence, evidence_desc)
        self.pattern = re.compile(pattern)
        self.redact = redact
        self.redact_char = redact_char

    def evaluate(self, context: dict[str, Any]) -> list[Evidence]:
        text = context.get("text", "")
        if not text:
            return []

        evidences = []
        # Find all non-overlapping matches
        for match in self.pattern.finditer(text):
            val = match.group(0)
            redacted = self._redact(val) if self.redact else None

            # Contextual validation for things like credit cards (Luhn check) could go here
            # For this phase, we rely on the regex

            evidences.append(
                Evidence(
                    source="regex",
                    rule=self.name,
                    category=self.category,
                    confidence=self.confidence,
                    redacted_value=redacted,
                    description=self.evidence_desc
                )
            )

            # Limit the number of evidence items for a single rule to avoid blowing up memory
            if len(evidences) >= 10:
                break

        return evidences

    def _redact(self, value: str) -> str:
        if len(value) <= 4:
            return self.redact_char * len(value)
        return self.redact_char * (len(value) - 4) + value[-4:]


class StructuredDataRule(ClassificationRule):
    """Matches sensitive columns in structured data (CSV)."""

    def __init__(self, column: str, category: str, confidence: float):
        super().__init__(f"column_{column}", category, confidence, f"Sensitive column name matched: {column}")
        self.column = column.lower()

    def evaluate(self, context: dict[str, Any]) -> list[Evidence]:
        headers = context.get("headers", [])
        for header in headers:
            if self.column in header.lower():
                return [
                    Evidence(
                        source="structured_data",
                        rule=self.name,
                        category=self.category,
                        confidence=self.confidence,
                        description=self.evidence_desc
                    )
                ]
        return []
