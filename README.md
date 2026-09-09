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

| Component | Description |
|-----------|-------------|
| **Endpoint Agent** | Native Windows service monitoring file operations, USB events, and network activity |
| **Central Server** | FastAPI backend providing REST API, event processing, and policy management |
| **Database** | SQLite (dev) / PostgreSQL (prod) for events, policies, and audit logs |
| **Dashboard** | React-based SOC interface for administrators |
| **ML Engine** | Behavioral analytics and anomaly detection (future) |

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic 2.x, Uvicorn |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router, Axios |
| Agent | Python, watchdog, psutil, pathlib |
| ML | scikit-learn, pandas, numpy, joblib |
| Database | SQLite (dev), PostgreSQL (prod) |
| Infrastructure | Docker, Docker Compose |
| Testing | pytest, pytest-asyncio, httpx |

## Repository Structure

```
sentinelx/
├── backend/          # FastAPI central server
│   ├── app/
│   │   ├── api/          # Versioned API routes
│   │   ├── db/           # Database models and engine
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic layer
│   │   ├── security/     # Authentication and authorization
│   │   └── realtime/     # WebSocket and event streaming
│   └── tests/
├── agent/            # Endpoint monitoring agent
│   ├── sentinel_agent/
│   │   ├── monitoring/       # File and system monitoring
│   │   ├── classification/   # Data sensitivity classification
│   │   ├── risk/             # Risk assessment engine
│   │   ├── policy/           # Policy evaluation
│   │   ├── enforcement/      # Action enforcement
│   │   ├── transport/        # Server communication
│   │   └── storage/          # Local event storage
│   └── tests/
├── frontend/         # React administrator dashboard
├── ml/               # Machine learning models and training
├── simulator/        # Test data and scenario simulation
├── scripts/          # Utility and deployment scripts
├── protected_data/   # Sample classified data (by sensitivity level)
├── docs/             # Project documentation
└── tests/            # Integration tests
```

## Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18+ and npm
- **Docker** and Docker Compose (optional, for PostgreSQL)
- **Windows 10/11** (for the endpoint agent)

## Setup

### 1. Clone and Configure

```bash
git clone <repository-url>
cd sentinelx
cp .env.example .env
# Edit .env with your configuration
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install backend dependencies
pip install -e ".[backend,dev]"

# Start the server
cd backend
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

### 4. Agent Setup

```bash
# Install agent dependencies
pip install -e ".[agent]"

# Run the agent
cd agent
python -m sentinel_agent
```

### 5. Docker Setup (Optional)

```bash
# Start PostgreSQL and backend
docker compose up -d postgres

# Update DATABASE_URL in .env to use PostgreSQL:
# DATABASE_URL=postgresql://sentinelx:changeme@localhost:5432/sentinelx
```

### 6. Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend build verification
cd frontend
npm run build
```

## Development Status

> **Current Phase: Phase 0 — Foundation**

### What Works Now

- ✅ Backend server starts and serves FastAPI docs
- ✅ Health endpoint with real database connectivity check
- ✅ Environment-based configuration
- ✅ Structured logging
- ✅ Database initialization (SQLite)
- ✅ Frontend application shell with routing
- ✅ Frontend ↔ Backend health connectivity
- ✅ Agent starts and shuts down cleanly
- ✅ Docker Compose configuration

### Not Yet Implemented

- ⬜ User authentication and authorization
- ⬜ Security event monitoring and capture
- ⬜ Data sensitivity classification
- ⬜ Risk assessment engine
- ⬜ Policy management and enforcement
- ⬜ USB device monitoring and control
- ⬜ File transfer blocking
- ⬜ Machine learning models
- ⬜ Real-time WebSocket events
- ⬜ Complete administrator dashboard
- ⬜ Two-endpoint demonstration setup

These features are planned for Phases 1–10. See `docs/implementation_plan.md` for the full roadmap.

## License

MIT — see [LICENSE](LICENSE) for details.
