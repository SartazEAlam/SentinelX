"""Data sensitivity classification.

Features:
- Hybrid classification (Rules + ML)
- Configurable deterministic rules (Regex, Keywords, Filenames, Extensions)
- Scikit-learn ML fallback
- File content and structured data extraction
"""

from sentinel_agent.classification.engine import ClassificationEngine
from sentinel_agent.classification.ml.models import MLClassifier
from sentinel_agent.classification.result import ClassificationResult, Evidence, SensitivityLevel

__all__ = [
    "ClassificationEngine",
    "MLClassifier",
    "ClassificationResult",
    "Evidence",
    "SensitivityLevel",
]
