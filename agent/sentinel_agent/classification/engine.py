"""Core classification engine orchestrator."""

import json
import logging
from pathlib import Path
from typing import Any

from sentinel_agent.classification.extractors.csv_extractor import CSVExtractor
from sentinel_agent.classification.extractors.text import TextExtractor
from sentinel_agent.classification.ml.models import MLClassifier
from sentinel_agent.classification.result import ClassificationResult, Evidence, SensitivityLevel
from sentinel_agent.classification.rules.matchers import (
    ExtensionRule,
    FilenameRule,
    KeywordRule,
    RegexRule,
    StructuredDataRule,
)

logger = logging.getLogger(__name__)


class ClassificationEngine:
    """Orchestrates the classification pipeline."""

    def __init__(self, config_path: Path, ml_dir: Path | None = None):
        self.config_path = config_path
        self.ml_dir = ml_dir
        self.rules: list[Any] = []
        self.sensitivity_levels: dict[str, int] = {}
        self.ml_classifier: MLClassifier | None = None

        self.text_extractor = TextExtractor()
        self.csv_extractor = CSVExtractor()

        self.version = "3.0.0"
        self.load_config()

        if self.ml_dir:
            self.ml_classifier = MLClassifier(self.ml_dir)
            self.ml_classifier.load()

    def load_config(self) -> None:
        """Load and parse the JSON configuration."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)

            self.sensitivity_levels = config.get(
                "sensitivity_levels",
                {
                    "UNKNOWN": 0,
                    "PUBLIC": 10,
                    "INTERNAL": 30,
                    "CONFIDENTIAL": 60,
                    "HIGHLY_CONFIDENTIAL": 90,
                },
            )

            rules_config = config.get("rules", {})

            # Load extension rules
            for ext, details in rules_config.get("extensions", {}).items():
                self.rules.append(
                    ExtensionRule(
                        ext, details["category"], details["confidence"], details["evidence"]
                    )
                )

            # Load filename rules
            for rule in rules_config.get("filenames", []):
                self.rules.append(
                    FilenameRule(
                        rule["pattern"], rule["category"], rule["confidence"], rule["evidence"]
                    )
                )

            # Load keyword rules
            for rule in rules_config.get("keywords", []):
                self.rules.append(
                    KeywordRule(
                        rule["keyword"], rule["category"], rule["confidence"], rule["evidence"]
                    )
                )

            # Load regex rules
            for rule in rules_config.get("regex", []):
                self.rules.append(
                    RegexRule(
                        rule["name"],
                        rule["pattern"],
                        rule["category"],
                        rule["confidence"],
                        rule["evidence"],
                        rule.get("redact", True),
                        rule.get("redact_char", "*"),
                    )
                )

            # Load structured data rules
            sensitive_cols = rules_config.get("structured_data", {}).get("sensitive_columns", {})
            for col, details in sensitive_cols.items():
                self.rules.append(
                    StructuredDataRule(col, details["category"], details["confidence"])
                )

            logger.info("Classification engine loaded %d rules", len(self.rules))
        except Exception as exc:
            logger.error("Failed to load classification config: %s", exc)

    def classify_file(self, file_path: Path) -> ClassificationResult:
        """Classify a file by path."""
        if not file_path.exists():
            return self._unknown_result("FILE_NOT_FOUND")

        # Handle dotfiles correctly (e.g. .env)
        ext = file_path.suffix.lower()
        if not ext and file_path.name.startswith("."):
            ext = file_path.name.lower()

        context: dict[str, Any] = {
            "filename": file_path.name,
            "extension": ext,
        }

        # 1. Extraction
        extraction = {}
        if context["extension"] == ".csv":
            extraction = self.csv_extractor.extract(file_path)
        else:
            extraction = self.text_extractor.extract(file_path)

        context.update(extraction)

        # 2. Rule Evaluation
        evidences: list[Evidence] = []
        for rule in self.rules:
            try:
                matches = rule.evaluate(context)
                evidences.extend(matches)
            except Exception as exc:
                logger.debug("Rule %s failed: %s", rule.name, exc)

        # 3. ML Evaluation (Optional fallback)
        ml_pred = None
        if self.ml_classifier and self.ml_classifier.is_loaded and context.get("text"):
            ml_pred = self.ml_classifier.predict(context["text"])

        # 4. Aggregation
        return self._aggregate(evidences, ml_pred, context)

    def _aggregate(
        self, evidences: list[Evidence], ml_pred: dict[str, Any] | None, context: dict[str, Any]
    ) -> ClassificationResult:
        """Combine evidence and ML predictions into a final sensitivity level."""
        # Start with base score 0 (UNKNOWN)
        total_confidence = 0.0
        categories = set()

        # Determine score from rules
        if evidences:
            # We don't just sum confidence, we take max or combine intelligently
            max_confidence = max(e.confidence for e in evidences)

            # Boost if multiple different sources or categories are hit
            unique_sources = len(set(e.source for e in evidences))
            if unique_sources > 1:
                max_confidence = min(1.0, max_confidence + 0.1)

            total_confidence = max_confidence

            for e in evidences:
                categories.add(e.category)

        # Incorporate ML prediction if rules didn't hit hard
        model_name = None
        model_version = None
        if ml_pred and ml_pred.get("prediction") != "UNKNOWN":
            ml_sens = ml_pred.get("prediction", "UNKNOWN")
            ml_score = self.sensitivity_levels.get(ml_sens, 0)

            # If ML says it's very sensitive but rules found nothing, we trust ML partially
            rule_sens = self._score_to_level(total_confidence * 100)
            rule_score = self.sensitivity_levels.get(rule_sens, 0)

            if ml_score > rule_score:
                # Use ML level but record it as evidence
                prob = ml_pred.get("probabilities", {}).get(ml_sens, 0.5)
                evidences.append(
                    Evidence(
                        source="ml",
                        rule=ml_pred.get("model_name", "model"),
                        category="OTHER_SENSITIVE",
                        confidence=prob,
                        description=f"ML model predicted {ml_sens}",
                    )
                )
                total_confidence = max(total_confidence, prob)

            model_name = ml_pred.get("model_name")
            model_version = ml_pred.get("model_version")

        final_level = self._score_to_level(total_confidence * 100)

        # If no evidence and ML didn't flag, but file is text, it's public/internal
        if final_level == SensitivityLevel.UNKNOWN and context.get("text"):
            final_level = SensitivityLevel.PUBLIC

        return ClassificationResult(
            sensitivity_level=final_level,
            confidence=round(total_confidence, 2),
            categories=list(categories),
            evidence=evidences,
            content_inspected=context.get("inspected", False),
            inspection_complete=context.get("complete", False),
            classifier_version=self.version,
            model_name=model_name,
            model_version=model_version,
        )

    def _score_to_level(self, score: float) -> SensitivityLevel:
        """Map a 0-100 score to a SensitivityLevel."""
        if score >= 90:
            return SensitivityLevel.HIGHLY_CONFIDENTIAL
        if score >= 60:
            return SensitivityLevel.CONFIDENTIAL
        if score >= 30:
            return SensitivityLevel.INTERNAL
        if score > 0:
            return SensitivityLevel.PUBLIC
        return SensitivityLevel.UNKNOWN

    def _unknown_result(self, reason: str) -> ClassificationResult:
        """Return an unknown result for failures."""
        return ClassificationResult(
            sensitivity_level=SensitivityLevel.UNKNOWN,
            confidence=0.0,
            evidence=[
                Evidence(
                    source="system",
                    rule="failure",
                    category="UNKNOWN",
                    confidence=0.0,
                    description=f"Classification failed: {reason}",
                )
            ],
            classifier_version=self.version,
        )
