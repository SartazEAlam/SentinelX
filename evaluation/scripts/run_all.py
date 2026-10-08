"""Master Evaluation Pipeline for SentinelX Phase 9.

Orchestrates the entire Phase 9 scientific evaluation:
  1. Loads synthetic dataset and stratified splits (zero data leakage)
  2. Evaluates Rule-Based Classifier
  3. Evaluates Logistic Regression (TF-IDF)
  4. Evaluates Random Forest (TF-IDF)
  5. Evaluates TF-IDF Representation & Vocabulary
  6. Evaluates SentinelX Hybrid Engine
  7. Evaluates Risk Scoring & Policy Enforcement Engine
  8. Measures End-to-End Latency across full event lifecycle
  9. Measures Process & System Resource Usage with psutil
  10. Generates publication-quality charts and confusion matrices
  11. Exports machine-readable metrics.json and error_analysis.json
  12. Prints comprehensive scientific comparison table
"""

import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from evaluation.scripts.data_loader import get_train_test_split, load_dataset
from evaluation.scripts.evaluate_rule_based import evaluate_rule_based
from evaluation.scripts.evaluate_logistic_regression import evaluate_logistic_regression
from evaluation.scripts.evaluate_random_forest import evaluate_random_forest
from evaluation.scripts.evaluate_tfidf import evaluate_tfidf
from evaluation.scripts.evaluate_hybrid import evaluate_hybrid
from evaluation.scripts.evaluate_risk_policy import evaluate_risk_and_policy
from evaluation.scripts.evaluate_end_to_end import evaluate_end_to_end_latency
from evaluation.scripts.evaluate_resources import evaluate_resource_usage
from evaluation.scripts.generate_plots import generate_all_plots


def run_full_evaluation() -> dict[str, Any]:
    """Executes the complete scientific evaluation suite."""
    print("=" * 80)
    print("SentinelX Phase 9: Evaluation and Analysis Pipeline Starting")
    print(f"Timestamp: {datetime.now(UTC).isoformat()}")
    print("=" * 80)

    base_dir = Path(__file__).resolve().parent.parent.parent
    results_dir = base_dir / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Dataset & Splits
    print("\n[1/9] Loading synthetic dataset and verifying train/test split...")
    dataset = load_dataset()
    train_samples, test_samples = get_train_test_split()
    print(f"      Total Samples: {len(dataset)} | Train: {len(train_samples)} (70%) | Test: {len(test_samples)} (30%)")

    # 2. Rule-Based Evaluation
    print("\n[2/9] Evaluating Rule-Based Engine...")
    rule_results = evaluate_rule_based(test_samples=test_samples)
    print(f"      Accuracy: {rule_results['accuracy']*100:.2f}% | Precision: {rule_results['precision']*100:.2f}% | Recall: {rule_results['recall']*100:.2f}% | F1: {rule_results['f1']:.4f}")

    # 3. Logistic Regression Evaluation
    print("\n[3/9] Evaluating Logistic Regression (TF-IDF)...")
    lr_results = evaluate_logistic_regression(train_samples=train_samples, test_samples=test_samples)
    print(f"      Accuracy: {lr_results['accuracy']*100:.2f}% | Precision: {lr_results['precision']*100:.2f}% | Recall: {lr_results['recall']*100:.2f}% | F1: {lr_results['f1']:.4f}")

    # 4. Random Forest Evaluation
    print("\n[4/9] Evaluating Random Forest (TF-IDF)...")
    rf_results = evaluate_random_forest(train_samples=train_samples, test_samples=test_samples)
    print(f"      Accuracy: {rf_results['accuracy']*100:.2f}% | Precision: {rf_results['precision']*100:.2f}% | Recall: {rf_results['recall']*100:.2f}% | F1: {rf_results['f1']:.4f}")

    # 5. TF-IDF Representation Evaluation
    print("\n[5/9] Evaluating TF-IDF Vocabulary and Feature Importance...")
    tfidf_results = evaluate_tfidf(train_samples=train_samples)
    print(f"      Vocabulary Size: {tfidf_results['vocabulary_size']} features | Matrix Sparsity: {tfidf_results['sparsity_percent']}%")

    # 6. Hybrid Approach Evaluation
    print("\n[6/9] Evaluating SentinelX Hybrid Engine (Rules + ML)...")
    hybrid_results = evaluate_hybrid(test_samples=test_samples)
    print(f"      Accuracy: {hybrid_results['accuracy']*100:.2f}% | Precision: {hybrid_results['precision']*100:.2f}% | Recall: {hybrid_results['recall']*100:.2f}% | F1: {hybrid_results['f1']:.4f}")

    # 7. Risk & Policy Evaluation
    print("\n[7/9] Evaluating RiskEngine & PolicyEngine on Operational Scenarios...")
    risk_policy_results = evaluate_risk_and_policy()
    print(f"      Pass Rate: {risk_policy_results['passed_scenarios']}/{risk_policy_results['total_scenarios']} ({risk_policy_results['pass_rate_percent']}%)")

    # 8. End-to-End Latency Evaluation
    print("\n[8/9] Measuring Multi-Stage End-to-End Pipeline Latencies...")
    e2e_results = evaluate_end_to_end_latency(num_samples=100)
    print(f"      Classification: {e2e_results['stages']['classification']['mean_ms']} ms | Risk: {e2e_results['stages']['risk_evaluation']['mean_ms']} ms | Policy: {e2e_results['stages']['policy_evaluation']['mean_ms']} ms | DB: {e2e_results['stages']['backend_db_ingestion']['mean_ms']} ms")
    print(f"      Total End-to-End Mean Latency: {e2e_results['stages']['total_end_to_end']['mean_ms']} ms (P95: {e2e_results['stages']['total_end_to_end']['p95_ms']} ms)")

    # 9. Resource Usage Evaluation
    print("\n[9/9] Measuring Process Resource Utilization (CPU, RAM, Disk)...")
    resource_results = evaluate_resource_usage(num_events=200)
    print(f"      CPU Active: {resource_results['cpu_usage']['active_percent']}% | RAM Loaded: {resource_results['memory_usage']['engine_loaded_rss_mb']} MB (Peak: {resource_results['memory_usage']['peak_rss_mb']} MB)")
    print(f"      Disk: Models={resource_results['disk_overhead']['models_dir_kb']} KB, Rules={resource_results['disk_overhead']['rules_config_kb']} KB, DB={resource_results['disk_overhead']['database_kb']} KB")

    # Master Metrics Object
    master_metrics = {
        "metadata": {
            "project": "SentinelX",
            "phase": "Phase 9 — Evaluation and Analysis",
            "timestamp": datetime.now(UTC).isoformat(),
            "total_dataset_samples": len(dataset),
            "train_samples": len(train_samples),
            "test_samples": len(test_samples),
            "random_seed": 42,
            "hardware": resource_results["environment"],
        },
        "rule_based": rule_results,
        "logistic_regression": lr_results,
        "random_forest": rf_results,
        "tfidf": tfidf_results,
        "hybrid": hybrid_results,
        "risk_and_policy": risk_policy_results,
        "end_to_end": e2e_results,
        "resource_usage": resource_results,
    }

    # Extract Error Analysis
    print("\n[+] Compiling Detailed Error Analysis...")
    error_analysis = {
        "summary": {
            "rule_based_false_positives": len(rule_results.get("false_positive_cases", [])),
            "rule_based_false_negatives": len(rule_results.get("false_negative_cases", [])),
            "hybrid_false_positives": len(hybrid_results.get("false_positive_cases", [])),
            "hybrid_false_negatives": len(hybrid_results.get("false_negative_cases", [])),
        },
        "rule_based_errors": {
            "false_positives": rule_results.get("false_positive_cases", []),
            "false_negatives": rule_results.get("false_negative_cases", []),
        },
        "hybrid_errors": {
            "false_positives": hybrid_results.get("false_positive_cases", []),
            "false_negatives": hybrid_results.get("false_negative_cases", []),
        },
    }

    # Save Machine-Readable JSONs
    metrics_path = results_dir / "metrics.json"
    error_path = results_dir / "error_analysis.json"

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(master_metrics, f, indent=2)
    with open(error_path, "w", encoding="utf-8") as f:
        json.dump(error_analysis, f, indent=2)

    print(f"      Saved machine-readable metrics: {metrics_path}")
    print(f"      Saved error analysis: {error_path}")

    # Generate Figures
    print("\n[+] Generating Publication-Quality Figures & Charts...")
    generate_all_plots(master_metrics)

    # Print Final Summary Comparison Table
    print("\n" + "=" * 95)
    print("                      SENTINELX PHASE 9: FINAL MODEL COMPARISON TABLE")
    print("=" * 95)
    header = f"{'Model':<22} | {'Accuracy':<9} | {'Precision':<9} | {'Recall':<9} | {'F1-Score':<9} | {'FPR':<7} | {'FNR':<7} | {'Latency':<10}"
    print(header)
    print("-" * 95)

    models_to_print = [
        ("Rule-Based", rule_results),
        ("Logistic Regression", lr_results),
        ("Random Forest", rf_results),
        ("SentinelX Hybrid", hybrid_results),
    ]

    for name, r in models_to_print:
        acc = f"{r.get('accuracy', 0.0)*100:.2f}%"
        prec = f"{r.get('precision', 0.0)*100:.2f}%"
        rec = f"{r.get('recall', 0.0)*100:.2f}%"
        f1 = f"{r.get('f1', 0.0):.4f}"
        fpr = f"{r.get('false_positive_rate', 0.0)*100:.2f}%"
        fnr = f"{r.get('false_negative_rate', 0.0)*100:.2f}%"
        lat = f"{r.get('latency_ms', 0.0):.3f} ms"
        print(f"{name:<22} | {acc:<9} | {prec:<9} | {rec:<9} | {f1:<9} | {fpr:<7} | {fnr:<7} | {lat:<10}")

    print("=" * 95)
    print("Phase 9 Evaluation Pipeline Complete.")
    return master_metrics


if __name__ == "__main__":
    run_full_evaluation()
