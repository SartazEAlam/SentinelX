# SentinelX: Testing and Validation Guide

**Document Version:** 1.0.0 (Final Delivery)  
**Test Suite Status:** **176 Passed, 0 Failed, 0 Skipped (100% Pass Rate)**  

---

## 1. Testing Philosophy & Framework

SentinelX follows a rigorous test-driven validation strategy combining automated unit tests, integration test suites, asynchronous mock transports, and empirical system validation workflows.

- **Primary Test Runner:** `pytest` (v8.4.2)
- **Async Framework:** `pytest-asyncio` (v0.26.0)
- **HTTP Simulation:** `starlette.testclient.TestClient`
- **Database Isolation:** In-memory transactional SQLite fixtures with auto-rollback.

---

## 2. Test Suite Inventory

The project test suite contains **176 automated test cases** spanning the backend, agent, and evaluation modules:

| Test Module | Test Count | Scope |
| :--- | :---: | :--- |
| **`backend/tests/test_alerts.py`** | 2 | Alert lifecycle (`OPEN` $\to$ `ACK` $\to$ `RESOLVE`), filtering |
| **`backend/tests/test_approvals.py`** | 5 | Quarantined approval creation, approve/reject endpoints, conflicts |
| **`backend/tests/test_audit.py`** | 2 | Immutable administrative audit trail recording and filtering |
| **`backend/tests/test_auth.py`** | 4 | JWT authentication, password hashing, token validation, invalid credentials |
| **`backend/tests/test_devices.py`** | 3 | Endpoint registration, duplicate IDs, heartbeat updates |
| **`backend/tests/test_events.py`** | 8 | Event ingestion, schema validation, batching, duplicate prevention |
| **`backend/tests/test_health.py`** | 9 | System readiness probes, database connection health |
| **`backend/tests/test_phase4_integration.py`** | 10 | End-to-end integration across risk scoring and policy decisions |
| **`backend/tests/test_policies.py`** | 3 | Policy CRUD operations, validation rules, priority ordering |
| **`backend/tests/test_policy_engine.py`** | 17 | Priority-based matching, threshold conditions, default fallback |
| **`backend/tests/test_risk_engine.py`** | 29 | 8-factor score calculation, clamping, weighting, boundary tests |
| **`backend/tests/test_stats.py`** | 3 | Analytics aggregates, sensitivity counts, device summaries |
| **`backend/tests/test_system_validation.py`** | 4 | Phase 9 operational workflows (ALLOW, HOLD+Approve, HOLD+Deny, BLOCK) |
| **`backend/tests/test_users.py`** | 5 | User management, RBAC enforcement, role assignment |
| **`agent/tests/integration/test_classification.py`** | 4 | ClassificationEngine file extraction and regex integration |
| **`agent/tests/test_agent.py`** | 14 | SentinelAgent state machine, lifecycle, graceful shutdown |
| **`agent/tests/test_event_store.py`** | 8 | Local offline SQLite buffering, durability, uncommitted flushes |
| **`agent/tests/test_filesystem.py`** | 6 | Watchdog event capture, move operations, temporary ignore rules |
| **`agent/tests/test_identity.py`** | 9 | Device UUID persistence, token loading, fingerprint generation |
| **`agent/tests/test_pipeline.py`** | 17 | Normalizer, deduplicator, priority queue buffering, batch flushes |
| **`agent/tests/test_transport.py`** | 9 | HTTP client retries, exponential backoff, connection failures |
| **`agent/tests/test_usb.py`** | 5 | USB device attachment detection, removable media heuristics |
| **Total Test Count** | **176** | **100% Pass Rate** |

---

## 3. Executing Test Suites

### 3.1 Run Full Regression Suite
```bash
# In project root with .venv active:
pytest
```
*Expected Result:* `176 passed, 3 warnings in ~18s`.

### 3.2 Run Specific Component Tests
```bash
# Test Risk Engine factor calculations:
pytest backend/tests/test_risk_engine.py

# Test Policy Engine rule evaluation:
pytest backend/tests/test_policy_engine.py

# Test Endpoint Agent lifecycle and buffering:
pytest agent/tests/test_agent.py agent/tests/test_pipeline.py

# Test Approval Workflow:
pytest backend/tests/test_approvals.py
```

### 3.3 Run Phase 9 System Validation Workflows
```bash
pytest backend/tests/test_system_validation.py
```
This executes the 4 representative operational DLP demonstrations:
1. **Workflow A (Low Risk $\to$ ALLOW):** Normal business operation evaluated and permitted.
2. **Workflow B (Medium Risk $\to$ HOLD $\to$ Approved):** Quarantined file reviewed by SOC analyst and granted.
3. **Workflow C (Medium Risk $\to$ HOLD $\to$ Denied):** Quarantined file rejected by SOC analyst and permanently deleted.
4. **Workflow D (High Risk $\to$ BLOCK):** Critical secret exfiltration immediately prevented and security incident logged.

---

## 4. Phase 9 Scientific Evaluation Execution

```bash
# Run the complete automated evaluation pipeline:
python -m evaluation.run_all
```
This executes:
1. Stratified 70/30 split on the 600-sample synthetic corpus.
2. Rule-based model inference.
3. TF-IDF + Logistic Regression inference and threshold analysis.
4. TF-IDF + Random Forest inference.
5. TF-IDF vocabulary sparsity analysis.
6. SentinelX Hybrid Engine evaluation.
7. Risk & Policy operational scenario evaluation.
8. End-to-end millisecond latency profiling (100 runs).
9. Memory RSS and CPU profiling using `psutil` (200 events).
10. Figure generation saving 10 PNG charts to `docs/evaluation/`.
