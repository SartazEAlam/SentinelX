"""TF-IDF Representation Analysis for SentinelX Phase 9.

Analyzes vocabulary size, n-gram distribution, sparsity,
and top informative features for the TF-IDF vectorizer.
"""

from pathlib import Path
from typing import Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from evaluation.scripts.data_loader import get_train_test_split

def evaluate_tfidf(train_samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Analyzes TF-IDF feature extraction properties."""
    if train_samples is None:
        train_samples, _ = get_train_test_split()

    x_train = [s["text"] for s in train_samples]
    y_train = np.array([1 if s["is_sensitive"] else 0 for s in train_samples])

    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
    x_matrix = vectorizer.fit_transform(x_train)

    feature_names = np.array(vectorizer.get_feature_names_out())
    vocab_size = len(feature_names)
    matrix_shape = x_matrix.shape
    sparsity = 1.0 - (x_matrix.nnz / (matrix_shape[0] * matrix_shape[1]))

    # Top features by class mean TF-IDF weight
    sens_idx = np.where(y_train == 1)[0]
    ben_idx = np.where(y_train == 0)[0]

    mean_tfidf_sens = np.asarray(x_matrix[sens_idx].mean(axis=0)).flatten()
    mean_tfidf_ben = np.asarray(x_matrix[ben_idx].mean(axis=0)).flatten()

    top_sens_indices = np.argsort(mean_tfidf_sens)[::-1][:15]
    top_ben_indices = np.argsort(mean_tfidf_ben)[::-1][:15]

    top_sensitive_features = [
        {"feature": str(feature_names[i]), "weight": round(float(mean_tfidf_sens[i]), 4)}
        for i in top_sens_indices
    ]
    top_benign_features = [
        {"feature": str(feature_names[i]), "weight": round(float(mean_tfidf_ben[i]), 4)}
        for i in top_ben_indices
    ]

    return {
        "representation": "TF-IDF (Term Frequency - Inverse Document Frequency)",
        "ngram_range": [1, 2],
        "max_features": 2000,
        "vocabulary_size": vocab_size,
        "sample_count": matrix_shape[0],
        "matrix_shape": list(matrix_shape),
        "sparsity_percent": round(float(sparsity * 100), 2),
        "top_sensitive_features": top_sensitive_features,
        "top_benign_features": top_benign_features,
    }

if __name__ == "__main__":
    res = evaluate_tfidf()
    print("=== TF-IDF Representation Analysis ===")
    print(f"Vocabulary Size: {res['vocabulary_size']}")
    print(f"Matrix Sparsity: {res['sparsity_percent']}%")
    print("Top 5 Sensitive Features:", [f['feature'] for f in res['top_sensitive_features'][:5]])
    print("Top 5 Benign Features   :", [f['feature'] for f in res['top_benign_features'][:5]])
