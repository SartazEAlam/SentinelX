"""Resource Usage Evaluation for SentinelX Phase 9.

Measures real system and process resource overhead using psutil:
  1. System and Hardware Environment specifications
  2. Idle State Resource Usage (CPU %, Memory RSS MB)
  3. Active Workload Resource Usage (CPU %, Peak Memory RSS MB, Memory Delta)
  4. Disk Storage Overhead (Model files, rule configs, local SQLite database)
"""

import os
import platform
import sys
import time
from pathlib import Path
from typing import Any
import psutil

from sentinel_agent.classification.engine import ClassificationEngine
from app.services.risk_engine import RiskEngine, RiskContext
from app.services.policy_engine import PolicyEngine
from app.risk_policy_config.risk_config import get_default_risk_config
from app.risk_policy_config.policy_config import get_default_policy_config


def evaluate_resource_usage(num_events: int = 200) -> dict[str, Any]:
    """Measures real memory, CPU, and disk overhead under idle and active workloads."""
    proc = psutil.Process(os.getpid())

    # Environment specs
    env_info = {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "cpu_count": psutil.cpu_count(logical=True),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "python_version": sys.version.split()[0],
    }

    # 1. Idle baseline measurement (warm-up)
    proc.cpu_percent(interval=None)
    time.sleep(1.0)
    idle_cpu = proc.cpu_percent(interval=None)
    idle_mem_mb = round(proc.memory_info().rss / (1024 * 1024), 2)

    # 2. Disk storage footprints
    base_dir = Path(__file__).resolve().parent.parent.parent
    models_dir = base_dir / "agent" / "models"
    config_file = base_dir / "agent" / "classification_rules.json"
    db_file = base_dir / "backend" / "sentinelx.db"

    def get_dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

    disk_usage = {
        "models_dir_bytes": get_dir_size(models_dir),
        "models_dir_kb": round(get_dir_size(models_dir) / 1024, 2),
        "rules_config_bytes": get_dir_size(config_file),
        "rules_config_kb": round(get_dir_size(config_file) / 1024, 2),
        "database_bytes": get_dir_size(db_file),
        "database_kb": round(get_dir_size(db_file) / 1024, 2),
    }

    # 3. Active event processing workload
    classification_engine = ClassificationEngine(
        config_path=config_file,
        ml_dir=models_dir if models_dir.exists() else None,
    )
    risk_engine = RiskEngine(config=get_default_risk_config())
    policy_engine = PolicyEngine(config=get_default_policy_config())

    loaded_mem_mb = round(proc.memory_info().rss / (1024 * 1024), 2)

    sample_texts = [
        "Normal employee team chat log and weekly sync updates.",
        "Confidential financial statement: revenue $4,500,000, routing 021000021.",
        "Internal project roadmap with proprietary algorithm architecture.",
        "AWS secret access key AKIAIOSFODNN7EXAMPLE and private token credentials.",
    ]

    mem_samples = []
    t_start = time.perf_counter()
    proc.cpu_percent(interval=None)

    for i in range(num_events):
        text = sample_texts[i % len(sample_texts)]
        context = {
            "filename": f"event_{i}.txt",
            "extension": ".txt",
            "text": text,
            "inspected": True,
            "complete": True,
        }
        evidences = []
        for rule in classification_engine.rules:
            try:
                evidences.extend(rule.evaluate(context))
            except Exception:
                pass
        ml_pred = None
        if classification_engine.ml_classifier and classification_engine.ml_classifier.is_loaded:
            ml_pred = classification_engine.ml_classifier.predict(text)
        res = classification_engine._aggregate(evidences, ml_pred, context)

        sens_level = res.sensitivity_level.value if hasattr(res.sensitivity_level, "value") else str(res.sensitivity_level)
        risk_ctx = RiskContext(
            sensitivity_level=sens_level,
            sensitivity_categories=list(res.categories),
            classification_confidence=float(res.confidence),
            action_type="COPY",
            destination_type="LOCAL_TRUSTED",
            user_role="EMPLOYEE",
            device_trust="MANAGED",
            is_business_hours=True,
            is_weekend=False,
            file_size_bytes=len(text),
        )
        assessment = risk_engine.assess(risk_ctx)
        policy_engine.evaluate(risk_ctx, assessment)

        if i % 20 == 0:
            mem_samples.append(proc.memory_info().rss / (1024 * 1024))

    elapsed_s = time.perf_counter() - t_start
    active_cpu = proc.cpu_percent(interval=None)
    peak_mem_mb = round(max(mem_samples) if mem_samples else proc.memory_info().rss / (1024 * 1024), 2)
    final_mem_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
    mem_delta_mb = round(final_mem_mb - loaded_mem_mb, 2)
    throughput_eps = round(num_events / elapsed_s, 2) if elapsed_s > 0 else 0.0

    return {
        "environment": env_info,
        "workload": {
            "events_processed": num_events,
            "duration_seconds": round(elapsed_s, 3),
            "throughput_events_per_sec": throughput_eps,
        },
        "cpu_usage": {
            "idle_percent": round(idle_cpu, 2),
            "active_percent": round(active_cpu, 2),
        },
        "memory_usage": {
            "baseline_rss_mb": idle_mem_mb,
            "engine_loaded_rss_mb": loaded_mem_mb,
            "peak_rss_mb": peak_mem_mb,
            "final_rss_mb": final_mem_mb,
            "leak_growth_delta_mb": mem_delta_mb,
        },
        "disk_overhead": disk_usage,
    }


if __name__ == "__main__":
    res = evaluate_resource_usage(num_events=200)
    print("=== SentinelX Resource Usage Evaluation ===")
    print(f"Environment: {res['environment']['os']}, {res['environment']['cpu_count']} CPUs, {res['environment']['total_ram_gb']} GB RAM")
    print(f"CPU: Idle={res['cpu_usage']['idle_percent']}%, Active={res['cpu_usage']['active_percent']}%")
    print(f"Memory: Baseline={res['memory_usage']['baseline_rss_mb']} MB, Loaded={res['memory_usage']['engine_loaded_rss_mb']} MB, Peak={res['memory_usage']['peak_rss_mb']} MB, Delta={res['memory_usage']['leak_growth_delta_mb']} MB")
    print(f"Throughput: {res['workload']['throughput_events_per_sec']} events/sec over {res['workload']['events_processed']} events")
    print(f"Disk: Models={res['disk_overhead']['models_dir_kb']} KB, Rules={res['disk_overhead']['rules_config_kb']} KB, DB={res['disk_overhead']['database_kb']} KB")
