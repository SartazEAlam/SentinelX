"""End-to-End Latency Evaluation for SentinelX Phase 9.

Measures real execution latencies across every lifecycle stage of an event:
  1. Content Classification Latency (Hybrid Engine)
  2. Risk Scoring Latency (RiskEngine)
  3. Policy Evaluation Latency (PolicyEngine)
  4. Backend Ingestion & DB Persistence Latency (FastAPI + SQLite)
  5. Total End-to-End Pipeline Latency

Calculates mean, median, min, max, and P95 metrics from real timed executions.
"""

from pathlib import Path
import time
from typing import Any
from uuid import uuid4
import numpy as np

from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.database import engine, SessionLocal
from sentinel_agent.classification.engine import ClassificationEngine
from sentinel_agent.classification.result import ClassificationResult
from app.services.risk_engine import RiskEngine, RiskContext
from app.services.policy_engine import PolicyEngine
from app.risk_policy_config.risk_config import (
    get_default_risk_config,
    ActionType,
    DestinationType,
    DeviceTrustLevel,
    UserRiskRole,
)
from app.risk_policy_config.policy_config import get_default_policy_config


def classify_text_sample(
    engine: ClassificationEngine, text: str, filename: str = "doc.txt"
) -> ClassificationResult:
    """Evaluates rules and ML model, returning aggregated result."""
    ext = Path(filename).suffix.lower()
    context = {
        "filename": filename,
        "extension": ext,
        "text": text,
        "inspected": True,
        "complete": True,
    }
    evidences = []
    for rule in engine.rules:
        try:
            evidences.extend(rule.evaluate(context))
        except Exception:
            pass

    ml_pred = None
    if engine.ml_classifier and engine.ml_classifier.is_loaded:
        ml_pred = engine.ml_classifier.predict(text)

    return engine._aggregate(evidences, ml_pred, context)


def evaluate_end_to_end_latency(num_samples: int = 100) -> dict[str, Any]:
    """Measures end-to-end latency across all pipeline stages."""
    # 1. Initialize Engines
    base_dir = Path(__file__).resolve().parent.parent.parent
    config_path = base_dir / "agent" / "classification_rules.json"
    models_dir = base_dir / "agent" / "models"
    classification_engine = ClassificationEngine(
        config_path=config_path,
        ml_dir=models_dir if models_dir.exists() else None,
    )

    risk_engine = RiskEngine(config=get_default_risk_config())
    policy_engine = PolicyEngine(config=get_default_policy_config())

    # 2. Setup Backend TestClient & Register Test Device
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    dev_id = f"eval-dev-{uuid4().hex[:8]}"
    reg_resp = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": dev_id,
            "hostname": "eval-host",
            "ip_address": "127.0.0.1",
            "os": "Windows 11",
            "device_name": "Evaluation Endpoint",
            "operating_system": "Windows 11",
            "agent_version": "1.0.0",
        },
    )
    assert reg_resp.status_code == 201, f"Failed device registration: {reg_resp.text}"
    token = reg_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    sample_texts = [
        "Normal business memo regarding weekly engineering synchronization and planning.",
        "Confidential report: Employee salary table and bank routing numbers: 123456789.",
        "AWS API Secret Access Key: AKIAIOSFODNN7EXAMPLE and secret token wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY.",
        "Customer records spreadsheet: contact email john.doe@example.com with order details.",
    ]

    classification_latencies = []
    risk_latencies = []
    policy_latencies = []
    backend_db_latencies = []
    total_latencies = []

    for i in range(num_samples):
        text = sample_texts[i % len(sample_texts)]
        evt_id = f"eval-evt-{uuid4().hex[:8]}"

        t_start_total = time.perf_counter()

        # Stage 1: Content Extraction & Classification
        t0 = time.perf_counter()
        clf_result = classify_text_sample(classification_engine, text)
        t_clf = (time.perf_counter() - t0) * 1000.0  # ms
        classification_latencies.append(t_clf)

        sens_level = clf_result.sensitivity_level.value if hasattr(clf_result.sensitivity_level, "value") else str(clf_result.sensitivity_level)

        # Stage 2: Risk Scoring
        ctx = RiskContext(
            sensitivity_level=sens_level,
            sensitivity_categories=list(clf_result.categories),
            classification_confidence=float(clf_result.confidence),
            action_type=ActionType.EXTERNAL_UPLOAD if "CONFIDENTIAL" in sens_level else ActionType.READ,
            destination_type=DestinationType.PUBLIC_CLOUD if "CONFIDENTIAL" in sens_level else DestinationType.LOCAL_TRUSTED,
            destination_identifier="https://external-cloud.com/upload",
            user_role=UserRiskRole.EMPLOYEE,
            device_trust=DeviceTrustLevel.MANAGED,
            is_business_hours=True,
            is_weekend=False,
            file_size_bytes=len(text.encode("utf-8")),
        )
        t1 = time.perf_counter()
        assessment = risk_engine.assess(ctx)
        t_risk = (time.perf_counter() - t1) * 1000.0  # ms
        risk_latencies.append(t_risk)

        # Stage 3: Policy Evaluation
        t2 = time.perf_counter()
        policy_decision = policy_engine.evaluate(ctx, assessment)
        t_policy = (time.perf_counter() - t2) * 1000.0  # ms
        policy_latencies.append(t_policy)

        # Stage 4: Backend API Ingestion & DB Persistence
        payload = {
            "event_id": evt_id,
            "timestamp": "2026-10-08T12:00:00Z",
            "event_type": "FILE_ACCESS",
            "action": ctx.action_type,
            "file_name": "eval_document.txt",
            "file_path": "C:\\Docs\\eval_document.txt",
            "file_size": ctx.file_size_bytes,
            "sensitivity_level": sens_level,
            "risk_score": float(assessment.risk_score),
            "decision": policy_decision.decision,
            "metadata_json": {"categories": list(clf_result.categories)},
        }
        t3 = time.perf_counter()
        resp = client.post("/api/v1/events", headers=headers, json=payload)
        t_db = (time.perf_counter() - t3) * 1000.0  # ms
        assert resp.status_code == 201, f"Failed event ingestion: {resp.text}"
        backend_db_latencies.append(t_db)

        t_total = (time.perf_counter() - t_start_total) * 1000.0  # ms
        total_latencies.append(t_total)

    def stats(arr: list[float]) -> dict[str, float]:
        a = np.array(arr)
        return {
            "mean_ms": round(float(np.mean(a)), 3),
            "median_ms": round(float(np.median(a)), 3),
            "min_ms": round(float(np.min(a)), 3),
            "max_ms": round(float(np.max(a)), 3),
            "p95_ms": round(float(np.percentile(a, 95)), 3),
            "std_ms": round(float(np.std(a)), 3),
        }

    return {
        "num_samples": num_samples,
        "stages": {
            "classification": stats(classification_latencies),
            "risk_evaluation": stats(risk_latencies),
            "policy_evaluation": stats(policy_latencies),
            "backend_db_ingestion": stats(backend_db_latencies),
            "total_end_to_end": stats(total_latencies),
        },
    }


if __name__ == "__main__":
    results = evaluate_end_to_end_latency(num_samples=100)
    print("=== End-to-End Latency Evaluation (100 samples) ===")
    for stage, metrics in results["stages"].items():
        print(f"[{stage.upper()}]: Mean={metrics['mean_ms']}ms, Median={metrics['median_ms']}ms, P95={metrics['p95_ms']}ms, Min={metrics['min_ms']}ms, Max={metrics['max_ms']}ms")
