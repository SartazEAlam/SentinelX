"""Hybrid Classifier Evaluation for SentinelX Phase 9.

Evaluates the complete SentinelX ClassificationEngine (combining deterministic rules
and trained ML models via the actual _aggregate() logic) on the unseen test set.
"""

import time
from pathlib import Path
from typing import Any
from sklearn.metrics import roc_curve, precision_recall_curve, auc

from sentinel_agent.classification.engine import ClassificationEngine
from sentinel_agent.classification.result import SensitivityLevel
from evaluation.scripts.data_loader import get_train_test_split

def evaluate_hybrid(test_samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Evaluates SentinelX Hybrid classification engine."""
    if test_samples is None:
        _, test_samples = get_train_test_split()

    base_dir = Path(__file__).resolve().parent.parent.parent
    config_path = base_dir / "agent" / "classification_rules.json"
    ml_dir = base_dir / "agent" / "models"

    # Instantiate full ClassificationEngine with both rules and trained ML models
    engine = ClassificationEngine(config_path=config_path, ml_dir=ml_dir)

    y_true = []
    y_pred = []
    y_scores = []
    latencies = []
    sample_results = []
    category_stats = {}

    for sample in test_samples:
        text = sample["text"]
        filename = sample.get("filename", "document.txt")
        cat = sample.get("category", "UNKNOWN")
        is_sensitive = sample["is_sensitive"]
        y_true.append(1 if is_sensitive else 0)

        ext = Path(filename).suffix.lower()
        if not ext and filename.startswith("."):
            ext = filename.lower()
        context = {
            "filename": filename,
            "extension": ext,
            "text": text,
            "inspected": True,
            "complete": True,
        }

        # Measure latency of full hybrid classification
        t0 = time.perf_counter()
        
        # 1. Rule evaluation
        evidences = []
        for rule in engine.rules:
            try:
                matches = rule.evaluate(context)
                evidences.extend(matches)
            except Exception:
                pass

        # 2. ML evaluation
        ml_pred = None
        if engine.ml_classifier and engine.ml_classifier.is_loaded and context.get("text"):
            ml_pred = engine.ml_classifier.predict(context["text"])

        # 3. Hybrid Aggregation
        result = engine._aggregate(evidences, ml_pred, context)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0) # ms

        # In SentinelX, sensitive if level is INTERNAL, CONFIDENTIAL, or HIGHLY_CONFIDENTIAL
        # (or confidence > 0.30)
        is_pred_sensitive = result.sensitivity_level in (
            SensitivityLevel.INTERNAL,
            SensitivityLevel.CONFIDENTIAL,
            SensitivityLevel.HIGHLY_CONFIDENTIAL,
        ) or result.confidence >= 0.30

        pred_val = 1 if is_pred_sensitive else 0
        y_pred.append(pred_val)
        y_scores.append(float(result.confidence))

        # Track per-category stats
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0, "detected": 0}
        category_stats[cat]["total"] += 1
        if is_pred_sensitive:
            category_stats[cat]["detected"] += 1
        if (pred_val == 1 and is_sensitive) or (pred_val == 0 and not is_sensitive):
            category_stats[cat]["correct"] += 1

        sample_results.append({
            "id": sample["id"],
            "true_label": 1 if is_sensitive else 0,
            "predicted_label": pred_val,
            "confidence": result.confidence,
            "sensitivity_level": result.sensitivity_level.value,
            "category": cat,
            "evidence_count": len(result.evidence),
            "evidences": [e.description for e in result.evidence],
            "text_preview": text[:80] + ("..." if len(text) > 80 else ""),
        })

    # Metrics
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # ROC / PR curve
    fpr_curve, tpr_curve, _ = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr_curve, tpr_curve)

    prec_curve, rec_curve, _ = precision_recall_curve(y_true, y_scores)
    pr_auc = auc(rec_curve, prec_curve)

    false_positives = [s for s in sample_results if s["true_label"] == 0 and s["predicted_label"] == 1]
    false_negatives = [s for s in sample_results if s["true_label"] == 1 and s["predicted_label"] == 0]

    return {
        "model_name": "Hybrid (Rules + ML)",
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
        "category_stats": category_stats,
        "false_positive_cases": false_positives,
        "false_negative_cases": false_negatives,
        "y_true": y_true,
        "y_pred": y_pred,
        "y_probs": y_scores,
        "fpr_curve": [float(v) for v in fpr_curve],
        "tpr_curve": [float(v) for v in tpr_curve],
        "prec_curve": [float(v) for v in prec_curve],
        "rec_curve": [float(v) for v in rec_curve],
    }

if __name__ == "__main__":
    res = evaluate_hybrid()
    print("=== Hybrid Classifier Evaluation ===")
    print(f"Accuracy : {res['accuracy'] * 100:.2f}%")
    print(f"Precision: {res['precision'] * 100:.2f}%")
    print(f"Recall   : {res['recall'] * 100:.2f}%")
    print(f"F1 Score : {res['f1']:.4f}")
    print(f"ROC-AUC  : {res['roc_auc']:.4f}")
    print(f"TP: {res['true_positives']}, FP: {res['false_positives']}, TN: {res['true_negatives']}, FN: {res['false_negatives']}")
    print(f"Average Latency: {res['latency_ms']:.3f} ms")
