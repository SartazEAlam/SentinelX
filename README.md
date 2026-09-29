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
4. **Dashboard (`frontend/`)**: React-based SOC interface for administrators.
5. **Simulators (`simulator/`)**: Testing tools like the web upload simulator to demonstrate enforcement.

## Development Status

> **Current Status: Phase 5 (Enforcement & Prevention Layer) — Complete**

### Core Features Working Today:
- ✅ **Phase 1 (Backend Core)**: FastAPI server, SQLite/PostgreSQL DB auto-initialization, JWT Authentication, and Audit Logging.
- ✅ **Phase 2 (Endpoint Agent)**: Real-time file system monitoring, USB detection, and reliable async event queuing.
- ✅ **Phase 3 (Classification)**: PII/PHI pattern recognition and sensitivity classification engine.
- ✅ **Phase 4 (Risk Engine)**: Centralized policy evaluation and risk scoring framework.
- ✅ **Phase 5 (Enforcement)**: Real-time blocking, HOLD quarantine workflows, and secure staging.

*(See `docs/implementation_plan.md` for the full 10-phase roadmap).*

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
   pip install -e ".[backend,agent,dev]"
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
# In Git Bash:
python simulator/upload_server.py --drop-dir C:/tmp/sentinelx_upload_test
```
- Listens on `http://localhost:8080`.
- Intercepts and blocks high-risk uploads before they persist.

---

## Documentation

Full technical documentation is located in the `docs/` folder:
- **[Architecture](docs/architecture.md)**
- **[API Reference](docs/api.md)**
- **[Threat Model](docs/threat_model.md)**
- **[Demo Guide](docs/demo_guide.md)** (A step-by-step walkthrough of Phase 5 Enforcement)

## License

This software and associated documentation are the proprietary information of SentinelX. All Rights Reserved. See the [LICENSE](LICENSE) file for details.
