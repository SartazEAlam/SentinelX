"""Logistic Regression Evaluation for SentinelX Phase 9.

Trains a TF-IDF + Logistic Regression model on the training set
and evaluates on the unseen test set across multiple classification thresholds.
"""

import time
from pathlib import Path
from typing import Any
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve, precision_recall_curve, auc

from evaluation.scripts.data_loader import get_train_test_split

def train_logistic_regression(train_samples: list[dict[str, Any]]):
    """Trains TF-IDF + Logistic Regression on train_samples."""
    x_train = [s["text"] for s in train_samples]
    y_train = [1 if s["is_sensitive"] else 0 for s in train_samples]

    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
    x_train_vec = vectorizer.fit_transform(x_train)

    model = LogisticRegression(random_state=42, max_iter=1000, C=1.0)
    model.fit(x_train_vec, y_train)

    return vectorizer, model

def evaluate_logistic_regression(
    threshold: float = 0.50,
    test_samples: list[dict[str, Any]] | None = None,
    train_samples: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluates Logistic Regression model on test set."""
    if train_samples is None or test_samples is None:
        train_samples, test_samples = get_train_test_split()

    vectorizer, model = train_logistic_regression(train_samples)

    x_test = [s["text"] for s in test_samples]
    y_true = [1 if s["is_sensitive"] else 0 for s in test_samples]

    # Save model artifact
    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"vectorizer": vectorizer, "model": model}, results_dir / "logistic_regression.joblib")

    # Latency and predictions
    t0 = time.perf_counter()
    x_test_vec = vectorizer.transform(x_test)
    y_probs = model.predict_proba(x_test_vec)[:, 1]
    t1 = time.perf_counter()
    avg_latency = ((t1 - t0) * 1000.0) / len(test_samples)

    # Threshold evaluation
    threshold_results = {}
    for th in [0.30, 0.40, 0.50, 0.60, 0.70]:
        th_pred = [1 if p >= th else 0 for p in y_probs]
        tp_th = sum(1 for yt, yp in zip(y_true, th_pred) if yt == 1 and yp == 1)
        tn_th = sum(1 for yt, yp in zip(y_true, th_pred) if yt == 0 and yp == 0)
        fp_th = sum(1 for yt, yp in zip(y_true, th_pred) if yt == 0 and yp == 1)
        fn_th = sum(1 for yt, yp in zip(y_true, th_pred) if yt == 1 and yp == 0)
        p_th = tp_th / (tp_th + fp_th) if (tp_th + fp_th) > 0 else 0.0
        r_th = tp_th / (tp_th + fn_th) if (tp_th + fn_th) > 0 else 0.0
        f1_th = 2 * p_th * r_th / (p_th + r_th) if (p_th + r_th) > 0 else 0.0
        threshold_results[str(th)] = {
            "threshold": th,
            "tp": tp_th,
            "tn": tn_th,
            "fp": fp_th,
            "fn": fn_th,
            "precision": round(p_th, 4),
            "recall": round(r_th, 4),
            "f1": round(f1_th, 4),
            "accuracy": round((tp_th + tn_th) / len(y_true), 4),
            "fpr": round(fp_th / (fp_th + tn_th) if (fp_th + tn_th) > 0 else 0.0, 4),
            "fnr": round(fn_th / (fn_th + tp_th) if (fn_th + tp_th) > 0 else 0.0, 4),
        }

    # Primary threshold
    y_pred = [1 if p >= threshold else 0 for p in y_probs]
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    total = len(y_true)
    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    # ROC / PR curve data
    fpr_curve, tpr_curve, _ = roc_curve(y_true, y_probs)
    roc_auc = auc(fpr_curve, tpr_curve)

    prec_curve, rec_curve, _ = precision_recall_curve(y_true, y_probs)
    pr_auc = auc(rec_curve, prec_curve)

    sample_results = []
    for s, yt, yp, prob in zip(test_samples, y_true, y_pred, y_probs):
        sample_results.append({
            "id": s["id"],
            "true_label": yt,
            "predicted_label": yp,
            "probability": round(float(prob), 4),
            "category": s.get("category", "UNKNOWN"),
            "text_preview": s["text"][:80] + ("..." if len(s["text"]) > 80 else ""),
        })

    false_positives = [s for s in sample_results if s["true_label"] == 0 and s["predicted_label"] == 1]
    false_negatives = [s for s in sample_results if s["true_label"] == 1 and s["predicted_label"] == 0]

    return {
        "model_name": "Logistic Regression",
        "threshold": threshold,
        "sample_count": total,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "roc_auc": round(float(roc_auc), 4),
        "pr_auc": round(float(pr_auc), 4),
        "latency_ms": round(avg_latency, 4),
        "threshold_analysis": threshold_results,
        "false_positive_cases": false_positives,
        "false_negative_cases": false_negatives,
        "y_true": y_true,
        "y_pred": y_pred,
        "y_probs": [float(p) for p in y_probs],
        "fpr_curve": [float(v) for v in fpr_curve],
        "tpr_curve": [float(v) for v in tpr_curve],
        "prec_curve": [float(v) for v in prec_curve],
        "rec_curve": [float(v) for v in rec_curve],
    }

if __name__ == "__main__":
    res = evaluate_logistic_regression()
    print("=== Logistic Regression Evaluation ===")
    print(f"Accuracy : {res['accuracy'] * 100:.2f}%")
    print(f"Precision: {res['precision'] * 100:.2f}%")
    print(f"Recall   : {res['recall'] * 100:.2f}%")
    print(f"F1 Score : {res['f1']:.4f}")
    print(f"ROC-AUC  : {res['roc_auc']:.4f}")
    print(f"TP: {res['true_positives']}, FP: {res['false_positives']}, TN: {res['true_negatives']}, FN: {res['false_negatives']}")
    print(f"Average Latency: {res['latency_ms']:.3f} ms")
