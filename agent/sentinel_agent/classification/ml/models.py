"""Lightweight ML classification component."""

import logging
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class MLClassifier:
    """Wrapper for TF-IDF and scikit-learn models to predict data sensitivity."""

    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.vectorizer: TfidfVectorizer | None = None
        self.model = None
        self.model_name = "unknown"
        self.model_version = "unknown"
        self.is_loaded = False

    def load(self) -> bool:
        """Load the vectorizer and model from disk."""
        try:
            vec_path = self.model_dir / "vectorizer.joblib"
            model_path = self.model_dir / "model.joblib"
            meta_path = self.model_dir / "metadata.joblib"

            if not (vec_path.exists() and model_path.exists()):
                logger.debug("ML models not found in %s", self.model_dir)
                return False

            self.vectorizer = joblib.load(vec_path)
            self.model = joblib.load(model_path)

            if meta_path.exists():
                meta = joblib.load(meta_path)
                self.model_name = meta.get("model_name", "unknown")
                self.model_version = meta.get("model_version", "unknown")

            self.is_loaded = True
            logger.info("Loaded ML model: %s (v%s)", self.model_name, self.model_version)
            return True
        except Exception as exc:
            logger.error("Failed to load ML models: %s", exc)
            return False

    def predict(self, text: str) -> dict[str, Any]:
        """Predict the sensitivity class of the text.
        
        Returns a dict with 'prediction' and 'probabilities'.
        """
        if not self.is_loaded or not self.vectorizer or not self.model:
            return {"prediction": "UNKNOWN", "probabilities": {}}

        if not text or not text.strip():
            return {"prediction": "UNKNOWN", "probabilities": {}}

        try:
            # Transform text
            X = self.vectorizer.transform([text])

            # Predict
            pred = self.model.predict(X)[0]

            # Get probabilities if supported
            probs = {}
            if hasattr(self.model, "predict_proba"):
                proba_array = self.model.predict_proba(X)[0]
                classes = self.model.classes_
                probs = {cls: float(prob) for cls, prob in zip(classes, proba_array)}

            return {
                "prediction": pred,
                "probabilities": probs,
                "model_name": self.model_name,
                "model_version": self.model_version
            }
        except Exception as exc:
            logger.error("ML prediction failed: %s", exc)
            return {"prediction": "UNKNOWN", "probabilities": {}}
