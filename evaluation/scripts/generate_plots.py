"""Plot Generator for SentinelX Phase 9 Evaluation.

Generates publication-quality charts and confusion matrices from real evaluation results:
  1. Confusion matrices (Rule-Based, Logistic Regression, Random Forest, Hybrid)
  2. ROC Curves (Logistic Regression, Random Forest, Hybrid)
  3. Precision-Recall Curves
  4. Model Performance Metrics Comparison (Accuracy, Precision, Recall, F1, FPR, FNR)
  5. Latency Comparison & End-to-End Pipeline Breakdown
  6. Decision Threshold Sensitivity Analysis
  7. System Resource Utilization Footprint
"""

import json
from pathlib import Path
from typing import Any
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def save_fig(fig: plt.Figure, name: str, base_dir: Path) -> None:
    """Saves figure in both evaluation/figures and docs/evaluation directories."""
    paths = [
        base_dir / "evaluation" / "figures" / name,
        base_dir / "docs" / "evaluation" / name,
    ]
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_confusion_matrices(results: dict[str, Any], base_dir: Path) -> None:
    """Generates styled confusion matrices for each evaluated model."""
    models = ["rule_based", "logistic_regression", "random_forest", "hybrid"]
    display_names = {
        "rule_based": "Rule-Based Engine",
        "logistic_regression": "Logistic Regression (TF-IDF)",
        "random_forest": "Random Forest (TF-IDF)",
        "hybrid": "SentinelX Hybrid Engine",
    }

    for model_key in models:
        data = results.get(model_key, {})
        cm = data.get("confusion_matrix")
        if not cm:
            tp = data.get("true_positives", 0)
            tn = data.get("true_negatives", 0)
            fp = data.get("false_positives", 0)
            fn = data.get("false_negatives", 0)
            if tp + tn + fp + fn == 0:
                continue
            cm = {
                "true_positives": tp,
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
            }

        fig, ax = plt.subplots(figsize=(6, 5))
        matrix = np.array([
            [cm["true_negatives"], cm["false_positives"]],
            [cm["false_negatives"], cm["true_positives"]],
        ])

        sns.heatmap(
            matrix,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=False,
            xticklabels=["Benign (0)", "Sensitive (1)"],
            yticklabels=["Benign (0)", "Sensitive (1)"],
            annot_kws={"size": 14, "weight": "bold"},
            ax=ax,
        )

        ax.set_title(f"Confusion Matrix: {display_names[model_key]}", fontsize=13, pad=12, weight="bold")
        ax.set_xlabel("Predicted Label", fontsize=11, labelpad=8)
        ax.set_ylabel("True Label", fontsize=11, labelpad=8)

        acc = data.get("accuracy", 0.0) * 100
        f1 = data.get("f1_score", data.get("f1", 0.0))
        plt.figtext(
            0.5, -0.05,
            f"Accuracy: {acc:.2f}%  |  F1-Score: {f1:.4f}  |  N = {data.get('sample_count', 180)}",
            ha="center", fontsize=10, style="italic"
        )

        save_fig(fig, f"confusion_matrix_{model_key}.png", base_dir)


def plot_metric_comparisons(results: dict[str, Any], base_dir: Path) -> None:
    """Generates comparison bar chart across models for Precision, Recall, F1, and Accuracy."""
    models = [
        ("Rule-Based", results.get("rule_based", {})),
        ("Logistic Regression", results.get("logistic_regression", {})),
        ("Random Forest", results.get("random_forest", {})),
        ("SentinelX Hybrid", results.get("hybrid", {})),
    ]

    labels = [m[0] for m in models]
    accuracies = [m[1].get("accuracy", 0.0) * 100 for m in models]
    precisions = [m[1].get("precision", 0.0) * 100 for m in models]
    recalls = [m[1].get("recall", 0.0) * 100 for m in models]
    f1_scores = [m[1].get("f1_score", m[1].get("f1", 0.0)) * 100 for m in models]

    x = np.arange(len(labels))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - 1.5 * width, accuracies, width, label="Accuracy (%)", color="#2b5c8f")
    ax.bar(x - 0.5 * width, precisions, width, label="Precision (%)", color="#38a169")
    ax.bar(x + 0.5 * width, recalls, width, label="Recall (%)", color="#e53e3e")
    ax.bar(x + 1.5 * width, f1_scores, width, label="F1-Score (%)", color="#805ad5")

    ax.set_ylabel("Score (%)", fontsize=12, labelpad=8)
    ax.set_title("Performance Comparison Across Classification Approaches", fontsize=14, weight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 115)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", frameon=True, fontsize=10)

    for i in range(len(labels)):
        ax.text(i + 1.5 * width, f1_scores[i] + 1.5, f"{f1_scores[i]:.1f}%", ha="center", fontsize=9, weight="bold")

    save_fig(fig, "model_metrics_comparison.png", base_dir)


def plot_error_rates(results: dict[str, Any], base_dir: Path) -> None:
    """Plots False Positive Rate (FPR) vs False Negative Rate (FNR)."""
    models = [
        ("Rule-Based", results.get("rule_based", {})),
        ("Logistic Regression", results.get("logistic_regression", {})),
        ("Random Forest", results.get("random_forest", {})),
        ("SentinelX Hybrid", results.get("hybrid", {})),
    ]

    labels = [m[0] for m in models]
    fpr = [m[1].get("false_positive_rate", 0.0) * 100 for m in models]
    fnr = [m[1].get("false_negative_rate", 0.0) * 100 for m in models]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, fpr, width, label="False Positive Rate (FPR %)", color="#dd6b20")
    ax.bar(x + width / 2, fnr, width, label="False Negative Rate (FNR %)", color="#e53e3e")

    ax.set_ylabel("Error Rate (%)", fontsize=12, labelpad=8)
    ax.set_title("False Positive Rate (FPR) vs False Negative Rate (FNR)", fontsize=13, weight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    max_val = max(max(fpr), max(fnr)) if max(fpr + fnr) > 0 else 10.0
    ax.set_ylim(0, max_val * 1.35)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=10)

    for i in range(len(labels)):
        ax.text(x[i] - width / 2, fpr[i] + 0.8, f"{fpr[i]:.1f}%", ha="center", fontsize=9)
        ax.text(x[i] + width / 2, fnr[i] + 0.8, f"{fnr[i]:.1f}%", ha="center", fontsize=9)

    save_fig(fig, "error_rates_comparison.png", base_dir)


def plot_latency_breakdown(results: dict[str, Any], base_dir: Path) -> None:
    """Plots inference latency comparison and End-to-End pipeline breakdown."""
    models = ["rule_based", "logistic_regression", "random_forest", "hybrid"]
    labels = ["Rule-Based", "Logistic Reg", "Random Forest", "Hybrid"]
    latencies = [results.get(m, {}).get("latency_ms", 0.0) for m in models]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    ax1.bar(labels, latencies, color=["#3182ce", "#38a169", "#d69e2e", "#805ad5"])
    ax1.set_ylabel("Latency (milliseconds)", fontsize=11)
    ax1.set_title("Classification Inference Latency per Sample", fontsize=12, weight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    for i, v in enumerate(latencies):
        ax1.text(i, v + (max(latencies) * 0.02), f"{v:.3f} ms", ha="center", fontsize=9, weight="bold")

    e2e = results.get("end_to_end", {}).get("stages", {})
    if e2e:
        stages = ["Classification", "Risk Eval", "Policy Eval", "DB Ingestion"]
        keys = ["classification", "risk_evaluation", "policy_evaluation", "backend_db_ingestion"]
        stage_means = [e2e.get(k, {}).get("mean_ms", 0.0) for k in keys]
        colors = ["#805ad5", "#3182ce", "#38a169", "#dd6b20"]

        ax2.bar(stages, stage_means, color=colors)
        ax2.set_ylabel("Mean Latency (milliseconds)", fontsize=11)
        ax2.set_title("End-to-End Event Processing Stage Breakdown", fontsize=12, weight="bold")
        ax2.grid(axis="y", linestyle="--", alpha=0.5)
        for i, v in enumerate(stage_means):
            ax2.text(i, v + (max(stage_means) * 0.02), f"{v:.2f} ms", ha="center", fontsize=9, weight="bold")

    save_fig(fig, "latency_comparison.png", base_dir)


def plot_roc_pr_curves(results: dict[str, Any], base_dir: Path) -> None:
    """Plots ROC and Precision-Recall Curves."""
    fig, (ax_roc, ax_pr) = plt.subplots(1, 2, figsize=(13, 5.5))

    models = [
        ("Logistic Regression", results.get("logistic_regression", {}), "#38a169"),
        ("Random Forest", results.get("random_forest", {}), "#d69e2e"),
        ("SentinelX Hybrid", results.get("hybrid", {}), "#805ad5"),
    ]

    for name, data, col in models:
        fpr = data.get("fpr_curve")
        tpr = data.get("tpr_curve")
        roc_auc = data.get("roc_auc", 0.0)
        precision = data.get("prec_curve")
        recall = data.get("rec_curve")
        pr_auc = data.get("pr_auc", 0.0)

        if fpr and tpr:
            ax_roc.plot(fpr, tpr, color=col, lw=2, label=f"{name} (AUC = {roc_auc:.4f})")
        if precision and recall:
            ax_pr.plot(recall, precision, color=col, lw=2, label=f"{name} (AUC = {pr_auc:.4f})")

    ax_roc.plot([0, 1], [0, 1], "k--", alpha=0.6, label="Chance Level (AUC = 0.50)")
    ax_roc.set_xlim([0.0, 1.0])
    ax_roc.set_ylim([0.0, 1.05])
    ax_roc.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    ax_roc.set_ylabel("True Positive Rate (Sensitivity)", fontsize=11)
    ax_roc.set_title("Receiver Operating Characteristic (ROC) Curves", fontsize=12, weight="bold")
    ax_roc.legend(loc="lower right", fontsize=9)
    ax_roc.grid(True, linestyle="--", alpha=0.5)

    ax_pr.set_xlim([0.0, 1.0])
    ax_pr.set_ylim([0.0, 1.05])
    ax_pr.set_xlabel("Recall", fontsize=11)
    ax_pr.set_ylabel("Precision", fontsize=11)
    ax_pr.set_title("Precision-Recall Curves", fontsize=12, weight="bold")
    ax_pr.legend(loc="lower left", fontsize=9)
    ax_pr.grid(True, linestyle="--", alpha=0.5)

    save_fig(fig, "roc_pr_curves.png", base_dir)


def plot_threshold_analysis(results: dict[str, Any], base_dir: Path) -> None:
    """Plots Precision, Recall, and F1 across decision thresholds."""
    lr_data = results.get("logistic_regression", {})
    t_analysis = lr_data.get("threshold_analysis", {})
    if not t_analysis:
        return

    items = list(t_analysis.values()) if isinstance(t_analysis, dict) else t_analysis
    thresholds = [t["threshold"] for t in items]
    precisions = [t["precision"] * 100 for t in items]
    recalls = [t["recall"] * 100 for t in items]
    f1s = [t["f1"] * 100 for t in items]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(thresholds, precisions, marker="o", label="Precision (%)", color="#38a169", lw=2)
    ax.plot(thresholds, recalls, marker="s", label="Recall (%)", color="#e53e3e", lw=2)
    ax.plot(thresholds, f1s, marker="^", label="F1-Score (%)", color="#805ad5", lw=2)

    ax.set_xlabel("Classification Decision Threshold", fontsize=11)
    ax.set_ylabel("Metric Score (%)", fontsize=11)
    ax.set_title("Classification Threshold vs Precision, Recall & F1 Trade-off", fontsize=13, weight="bold", pad=12)
    ax.set_xticks(thresholds)
    ax.set_ylim(80, 105)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower left", fontsize=10)

    save_fig(fig, "threshold_analysis.png", base_dir)


def plot_resource_usage(results: dict[str, Any], base_dir: Path) -> None:
    """Plots Memory RSS progression and Disk Footprint breakdown."""
    res_data = results.get("resource_usage", {})
    if not res_data:
        return

    mem = res_data.get("memory_usage", {})
    disk = res_data.get("disk_overhead", {})

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    labels = ["Idle Baseline", "Engines Loaded", "Peak Workload", "Final RSS"]
    values = [
        mem.get("baseline_rss_mb", 0.0),
        mem.get("engine_loaded_rss_mb", 0.0),
        mem.get("peak_rss_mb", 0.0),
        mem.get("final_rss_mb", 0.0),
    ]

    ax1.bar(labels, values, color=["#4a5568", "#3182ce", "#e53e3e", "#38a169"])
    ax1.set_ylabel("Memory RSS (Megabytes)", fontsize=11)
    ax1.set_title("Endpoint Agent Memory Consumption Profile", fontsize=12, weight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    for i, v in enumerate(values):
        ax1.text(i, v + 2, f"{v:.1f} MB", ha="center", fontsize=9, weight="bold")

    disk_labels = ["ML Models", "Local SQLite DB", "Rules Config"]
    disk_vals = [
        disk.get("models_dir_kb", 0.0),
        disk.get("database_kb", 0.0),
        disk.get("rules_config_kb", 0.0),
    ]
    ax2.bar(disk_labels, disk_vals, color=["#805ad5", "#dd6b20", "#319795"])
    ax2.set_ylabel("Storage Size (Kilobytes)", fontsize=11)
    ax2.set_title("SentinelX Component Disk Storage Overhead", fontsize=12, weight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    for i, v in enumerate(disk_vals):
        ax2.text(i, v + 15, f"{v:.1f} KB", ha="center", fontsize=9, weight="bold")

    save_fig(fig, "resource_usage.png", base_dir)


def generate_all_plots(results: dict[str, Any]) -> None:
    """Entrypoint to generate all figures for Phase 9."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    plot_confusion_matrices(results, base_dir)
    plot_metric_comparisons(results, base_dir)
    plot_error_rates(results, base_dir)
    plot_latency_breakdown(results, base_dir)
    plot_roc_pr_curves(results, base_dir)
    plot_threshold_analysis(results, base_dir)
    plot_resource_usage(results, base_dir)
    print("All Phase 9 evaluation figures generated successfully.")
