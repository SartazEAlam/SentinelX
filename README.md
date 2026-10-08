# SentinelX

**Intelligent Data Loss Prevention and Exfiltration Detection System**

---

## Overview

SentinelX is an enterprise-grade Data Loss Prevention (DLP) system designed to detect, classify, and prevent unauthorized exfiltration of sensitive data from Windows endpoints. 

It combines real-time file monitoring, behavioral analytics, machine learning, and policy-based enforcement to protect critical organizational data.

## Architecture & Components

SentinelX uses a client-server architecture:

1. **Endpoint Agent (`agent/`)**: Native Windows service monitoring file operations, USB events, and network activity. Enforces Blocks and Holds in real-time.
2. **Central Server (`backend/`)**: FastAPI backend providing REST API, event processing, risk scoring, and policy management.
3. **Database**: SQLite (dev) or PostgreSQL (prod) for events, policies, and audit logs. Automatically initialized on startup.
4. **Dashboard (`frontend/`)**: React-based SOC interface for administrators with live WebSockets.
5. **Simulators (`simulator/`)**: Testing tools like the web upload simulator to demonstrate enforcement.
6. **Evaluation Pipeline (`evaluation/`)**: Automated empirical evaluation suite testing classifiers, latency, and resource footprint.

## Development Status

> **Current Status: Phase 9 (Evaluation & Analysis) — Completed**  
> *(All 9 technical implementation phases of SentinelX are fully completed, tested, and verified).*

### Core Features Working Today:
- ✅ **Phase 1 (Backend Core)**: FastAPI server, DB auto-initialization, JWT Authentication, and Audit Logging.
- ✅ **Phase 2 (Endpoint Agent)**: Real-time file system monitoring, USB detection, and reliable async event queuing.
- ✅ **Phase 3 (Classification)**: PII/PHI pattern recognition and sensitivity classification engine.
- ✅ **Phase 4 (Risk Engine)**: Centralized policy evaluation and risk scoring framework.
- ✅ **Phase 5 (Enforcement)**: Real-time blocking, HOLD quarantine workflows, and secure staging.
- ✅ **Phase 6 (Dashboard Core)**: React frontend with Recharts analytics, real-time WebSockets.
- ✅ **Phase 7 (Admin Dashboard & Monitoring)**: Detailed views for Events, Devices, Policies, Enforcement, Approvals, Audit Logs, and Settings.
- ✅ **Phase 8 (Integration)**: Full End-to-End integration testing and verification.
- ✅ **Phase 9 (Evaluation & Analysis)**: Scientific evaluation comparing Rule-Based, Logistic Regression, Random Forest, and Hybrid classification; multi-factor risk and policy engine verification (100% pass rate); end-to-end latency profiling (<52 ms P95); resource usage benchmarking (<0.4 MB leak growth delta, 0.0% idle CPU); and comprehensive academic report.

---

## Quick Start (Local Development)

> **Important**: SentinelX is a monorepo. Use a **single virtual environment** at the project root (`SentinelX/.venv`). Do not create separate `.venv` folders in `backend/` or `agent/`.

### 1. Setup

1. **Environment Config**:
   ```bash
   cp .env.example .env
   ```
2. **Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Windows Git Bash
   # OR: .venv\Scripts\Activate.ps1 (Windows PowerShell)
   ```
3. **Install Dependencies**:
   ```bash
   pip install -e ".[backend,agent,ml,dev]"
   ```
4. **Seed Database** (Creates admin/analyst users and sample policies):
   ```bash
   python scripts/seed_dev.py
   ```
5. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

---

### 2. Running the System

You will need **4 separate terminal windows** (ensure your `.venv` is activated in the first 3).

#### Terminal 1: Backend Server
```bash
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```
- **API URL**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs

#### Terminal 2: Frontend Dashboard
```bash
cd frontend
npm run dev
```
- **Web Dashboard**: http://localhost:5173
- *Login with `admin` / `Admin@123!`*

#### Terminal 3: Endpoint Agent
```bash
python -m sentinel_agent
```
- Starts the local monitoring agent. Press `Ctrl + C` to stop.

#### Terminal 4: Upload Simulator (Phase 5 Demo)
Simulates an untrusted web application file upload to demonstrate SentinelX Enforcement.
```bash
python simulator/upload_server.py --drop-dir C:/tmp/sentinelx_upload_test
```
- Listens on `http://localhost:8080`.
- Intercepts and blocks high-risk uploads before they persist.

---

### 3. Running Evaluation & Tests

```bash
# Run the complete Phase 9 scientific evaluation suite and generate charts/metrics:
python -m evaluation.run_all

# Run Phase 9 system validation integration tests (ALLOW, HOLD, APPROVE, DENY, BLOCK):
pytest backend/tests/test_system_validation.py

# Run the complete project regression test suite:
pytest
```

---

## Documentation

Full technical documentation is located in the `docs/` folder:
- **[Evaluation and Analysis Report](docs/evaluation-and-analysis.md)** (Phase 9 Scientific Report with Tables and Charts)
- **[Architecture](docs/architecture.md)**
- **[API Reference](docs/api.md)**
- **[Threat Model](docs/threat_model.md)**
- **[Demo Guide](docs/demo_guide.md)** (A step-by-step walkthrough of Enforcement and Dashboard features)

## License

This software and associated documentation are the proprietary information of SentinelX. All Rights Reserved. See the [LICENSE](LICENSE) file for details.
