# SentinelX

**Intelligent Data Loss Prevention and Exfiltration Detection System**

---

## Overview

SentinelX is an enterprise-grade Data Loss Prevention (DLP) system designed to detect, classify, and prevent unauthorized exfiltration of sensitive data from Windows endpoints. It combines real-time file monitoring, behavioral analytics, machine learning, and policy-based enforcement to protect critical organizational data.

## Problem Statement

Organizations face increasing risk of data loss through:

- Unauthorized file transfers to USB drives and external media
- Sensitive data exfiltration via cloud services and email
- Insider threats from privileged users
- Accidental exposure of classified information

SentinelX addresses these challenges by providing an intelligent, multi-layered defense system that monitors endpoint activity, classifies data sensitivity, assesses risk in real-time, and enforces configurable security policies.

## Architecture

```
Protected Windows Endpoint
         |
         v
  SentinelX Endpoint Agent
         |
         |  HTTPS / REST
         v
  SentinelX Central Server
         |
         +---- Database (SQLite / PostgreSQL)
         |
         +---- Risk / Policy Services
         |
         +---- Realtime Events (WebSocket)
         |
         v
  Administrator Dashboard (React)
```

### Components

| Component          | Description                                                                         |
| ------------------ | ----------------------------------------------------------------------------------- |
| **Endpoint Agent** | Native Windows service monitoring file operations, USB events, and network activity |
| **Central Server** | FastAPI backend providing REST API, event processing, and policy management         |
| **Database**       | SQLite (dev) / PostgreSQL (prod) for events, policies, and audit logs               |
| **Dashboard**      | React-based SOC interface for administrators                                        |
| **ML Engine**      | Behavioral analytics and anomaly detection (future)                                 |

## Technology Stack

| Layer          | Technologies                                                 |
| -------------- | ------------------------------------------------------------ |
| Backend        | Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic 2.x, Uvicorn |
| Frontend       | React 19, TypeScript, Vite, Tailwind CSS v4, React Router, Axios |
| Agent          | Python, watchdog, psutil, pathlib                            |
| ML             | scikit-learn, pandas, numpy, joblib                          |
| Database       | SQLite (dev default), PostgreSQL (production)                |
| Infrastructure | Docker, Docker Compose                                       |
| Testing        | pytest, pytest-asyncio, httpx, oxlint                        |

## Repository Structure

```
sentinelx/
├── backend/          # FastAPI central server
│   ├── app/
│   │   ├── api/          # Versioned API routes (e.g., /api/v1/health)
│   │   ├── db/           # SQLAlchemy models and database engine
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic layer
│   │   ├── security/     # Authentication and authorization
│   │   └── realtime/     # WebSocket and event streaming
│   ├── Dockerfile        # Containerized backend deployment
│   └── tests/            # Backend unit & integration tests
├── agent/            # Endpoint monitoring agent
│   ├── sentinel_agent/
│   │   ├── monitoring/       # File, USB, and process monitoring
│   │   ├── classification/   # Sensitivity classification
│   │   ├── risk/             # Risk scoring engine
│   │   ├── policy/           # Policy evaluation
│   │   ├── enforcement/      # Action enforcement (block/warn/log)
│   │   ├── transport/        # Server communication
│   │   └── storage/          # Local event storage
│   └── tests/            # Agent lifecycle & config tests
├── frontend/         # React administrator dashboard
│   ├── src/
│   │   ├── pages/        # Dashboard, System Health, Events, etc.
│   │   ├── components/   # Layout, Sidebar, ErrorBoundary, etc.
│   │   └── services/     # Axios API client
├── ml/               # Machine learning models and training pipelines
├── simulator/        # Exfiltration simulation scripts and scenarios
├── scripts/          # Automation and development helpers
├── protected_data/   # Sample classified test files
├── docs/             # Technical specifications and guides
└── tests/            # End-to-end integration tests
```

## Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18+ and npm
- **Docker** and Docker Compose (optional, for containerized deployment)
- **Windows 10/11** (for the endpoint agent)

---

## Quick Start (Local Development)

> [!IMPORTANT]
> **Single Virtual Environment Rule**: SentinelX is a monorepo. You only need **one single virtual environment at the project root** (`SentinelX/.venv`). All components (Backend, Agent, CLI tools, tests) share this root environment. **Do not create `.venv` directories inside `backend/` or `agent/`**.

### 1. Environment Setup (One-Time)

Open a terminal at the project root directory (`SentinelX/`):

#### Step 1: Copy Environment Template
```bash
cp .env.example .env
```
*(On Windows PowerShell, you can also run `Copy-Item .env.example .env`)*

#### Step 2: Create the Virtual Environment (Root Only)
```bash
python -m venv .venv
```

#### Step 3: Activate the Virtual Environment
Choose the command matching your terminal:
- **PowerShell (Windows)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(If you get a script execution policy error, run once: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*
- **Command Prompt (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Git Bash / macOS / Linux**:
  ```bash
  source .venv/Scripts/activate
  ```

#### Step 4: Install Python Dependencies
Install Backend, Agent, and Dev dependencies in editable mode:
```bash
pip install -e ".[backend,agent,dev]"
```

#### Step 5: Seed the Development Database
Populates the local database with initial admin credentials, an analyst account, and sample security policies:
```bash
python scripts/seed_dev.py
```

#### Step 6: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

### 2. Running the System

Open **3 separate terminal windows** (with the root `.venv` activated for Terminals 1 and 3):

#### Terminal 1: Backend Server (FastAPI)
Run directly from the **project root** (recommended):
```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
```
*(Alternatively: `cd backend && uvicorn app.main:app --reload --port 8000`)*

- **API URL**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

#### Terminal 2: Frontend Dashboard (React + Vite)
From the **`frontend/`** directory:
```bash
cd frontend
npm run dev
```
- **Web Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Live System Health**: [http://localhost:5173/system-health](http://localhost:5173/system-health) *(verifies live backend & database connectivity)*

> [!TIP]
> **Default Login Credentials** (created by `scripts/seed_dev.py`):
> | Role | Username | Password |
> |---|---|---|
> | **Administrator** | `admin` | `Admin@123!` |
> | **Security Analyst** | `analyst_jane` | `AnalystPassword123!` |

#### Terminal 3: Endpoint Agent
Run from the **project root** with `.venv` activated:
```bash
python -m sentinel_agent
```
- Starts the endpoint agent service with active device session.
- Press `Ctrl + C` for graceful shutdown.

---

### 3. Docker Deployment (Alternative)

To run the containerized backend with a PostgreSQL database:

```bash
# From project root:
docker compose up -d

# Check running containers
docker compose ps

# View backend logs
docker compose logs -f backend

# Stop all containers
docker compose down
```

---

### 4. Running Tests & Quality Checks

Run all automated tests and linters from the **project root** with `.venv` activated:

```bash
# Run all Python tests (Backend + Agent: 42 tests)
pytest -v

# Run Python linter & code formatter check (Ruff)
ruff check .

# Run Frontend linter (Oxlint)
cd frontend && npm run lint && cd ..

# Run Frontend TypeScript & production build
cd frontend && npm run build && cd ..
```

---

## Documentation

Comprehensive project documentation is available in the [`docs/`](docs/) directory:

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | High-level system design, data flows, and security boundaries |
| [API Reference](docs/api.md) | REST API endpoints, schemas, and status codes |
| [Implementation Plan](docs/implementation_plan.md) | Phased implementation roadmap (Phases 0–10) |
| [Deployment Guide](docs/deployment.md) | Local and containerized deployment instructions |
| [Threat Model](docs/threat_model.md) | Threat vectors, assets, trust boundaries, and mitigations |
| [Testing Strategy](docs/testing.md) | Test organization, unit, integration, and verification procedures |
| [Known Limitations](docs/limitations.md) | Current phase boundaries and planned enhancements |
| [Demo Guide](docs/demo_guide.md) | Step-by-step walkthrough for demonstration |

---

## Development Status

> **Current Status: Phase 1 (Backend, Database, Authentication & Event Management) — Complete**

### What Works Now

- ✅ Backend server starts cleanly and serves interactive FastAPI docs
- ✅ Health endpoint (`/api/v1/health`) with live database connectivity verification
- ✅ Environment-based configuration via Pydantic Settings
- ✅ Structured contextual logging with automatic sensitive token redaction
- ✅ Database initialization (SQLite local default, PostgreSQL ready)
- ✅ Frontend application shell with responsive navigation and error boundary
- ✅ Live Frontend ↔ Backend health monitoring dashboard
- ✅ Endpoint Agent with session management and ASCII-safe Windows console support
- ✅ Docker Compose orchestration with healthchecked PostgreSQL and backend container
- ✅ Full automated test suite passing (42/42 tests, 0 lint errors, 0 type errors)
- ✅ **Phase 1 Complete**: Full Alembic database migrations, comprehensive Pydantic schemas, RBAC JWT Authentication, dual-layer endpoint device auth, and global Audit Logging service.

### Planned Roadmap (Phases 2–10)

- ✅ **Phase 1**: JWT Authentication, Device Registration, and Event Ingestion
- ⬜ **Phase 2**: Real-time File System Monitoring (`watchdog`)
- ⬜ **Phase 3**: Data Sensitivity Classification (Content & Metadata)
- ⬜ **Phase 4**: Multi-factor Risk Scoring Engine
- ⬜ **Phase 5**: Policy Evaluation & Enforcement Engine (Block / Warn / Allow)
- ⬜ **Phase 6**: SOC Administrator Dashboard (Live Events, Alerts, Policies)
- ⬜ **Phase 7**: USB Device Detection and Storage Control
- ⬜ **Phase 8**: Machine Learning Anomaly Detection
- ⬜ **Phase 9**: Comprehensive Integration & Stress Testing
- ⬜ **Phase 10**: End-to-End Exfiltration Simulation & Demo Script

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

