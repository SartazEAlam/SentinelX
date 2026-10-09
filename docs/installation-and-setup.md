# SentinelX: Installation and Setup Guide

**Document Version:** 1.0.0 (Final Delivery)  
**Target Audience:** DevOps, System Administrators, Evaluators, Reviewers  

---

## 1. System Requirements

### 1.1 Hardware Prerequisites
- **Minimum:** 4 Cores CPU, 8 GB RAM, 500 MB free disk space.
- **Recommended:** 8+ Cores CPU, 16 GB RAM, NVMe SSD storage.

### 1.2 Software Prerequisites
| Component | Supported Version | Purpose |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 / Windows 11 (64-bit) | Native agent monitoring |
| **Python** | Python 3.11.x (tested on 3.11.9) | Backend and Agent runtime |
| **Node.js** | Node.js 18.x or 20.x LTS | React / Vite Dashboard runtime |
| **npm** | npm 9.x or 10.x | Frontend package manager |
| **Git** | Git 2.40+ | Version control |

---

## 2. Repository Layout & Monorepo Rule

SentinelX is structured as a unified monorepo:
```
SentinelX/
├── .venv/                   # SINGLE shared virtual environment for the repo
├── agent/                   # Endpoint agent service (Windows monitoring)
├── backend/                 # FastAPI REST API, database, and business services
├── docs/                    # Complete architectural, manual, and evaluation docs
├── evaluation/              # Phase 9 scientific benchmark suite & datasets
├── frontend/                # React / TypeScript / Vite SOC Administrator Dashboard
├── simulator/               # Untrusted file upload simulator for demo testing
├── pyproject.toml           # Unified Python dependency specification
└── README.md                # Project landing documentation
```

> **CRITICAL RULE:** Use a **single Python virtual environment** at the root of `SentinelX/`. Do not create nested `.venv` folders inside `backend/` or `agent/`.

---

## 3. Single-Machine Installation (Local Development / Demonstration)

### Step 1: Clone and Prepare Environment
```bash
# 1. Clone repository
git clone https://github.com/SartazEAlam/SentinelX.git
cd SentinelX

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate virtual environment
# In Windows PowerShell:
.venv\Scripts\Activate.ps1
# OR in Git Bash:
source .venv/Scripts/activate
```

### Step 2: Install Python Dependencies
```bash
# Install all components including backend, agent, machine learning, and dev tooling:
pip install -e ".[backend,agent,ml,dev]"
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` settings for local testing:
```ini
ENVIRONMENT=development
DATABASE_URL=sqlite:///./sentinelx.db
JWT_SECRET_KEY=change-this-in-production-use-a-strong-secret-key-32chars
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
AGENT_SERVER_URL=http://localhost:8000
AGENT_MONITORING_MODE=STRICT
AGENT_PROTECTED_PATHS=C:/tmp/sentinelx_protected
AGENT_ENFORCEMENT_ENABLED=true
```

### Step 4: Initialize and Seed Database
```bash
python scripts/seed_dev.py
```
This populates:
- Initial Administrator account (`admin` / `Admin@123!`)
- SOC Analyst account (`analyst` / `Analyst@123!`)
- Default DLP Policy rules (`Block High Risk Exfiltration`, `Hold Medium Risk USB`, `Allow Low Risk Operations`)

### Step 5: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 4. Running the System (Local 4-Terminal Mode)

Open four separate terminals (ensure `.venv` is activated in Terminals 1, 3, and 4):

### Terminal 1: Backend API Server
```bash
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```
- **API Base:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`

### Terminal 2: SOC Administrator Dashboard
```bash
cd frontend
npm run dev
```
- **Web UI:** `http://localhost:5173`
- Log in with `admin` / `Admin@123!`

### Terminal 3: SentinelX Endpoint Agent
```bash
python -m sentinel_agent
```
- Automatically registers device, initiates file watchers, and runs event loop.

### Terminal 4: Upload Simulator (Enforcement Testing)
```bash
python simulator/upload_server.py --drop-dir C:/tmp/sentinelx_upload_test
```
- Listens on `http://localhost:8080` to simulate unauthorized web file drops.

---

## 5. Two-Laptop Network Setup (Distributed Topology)

To demonstrate SentinelX across physical network nodes:

### Laptop 1 (Protected Endpoint)
1. Ensure Python 3.11 and the `.venv` are prepared.
2. Edit `Laptop 1`'s `.env`:
   ```ini
   AGENT_SERVER_URL=http://<LAPTOP_2_IP>:8000
   AGENT_PROTECTED_PATHS=C:/tmp/sentinelx_protected
   AGENT_ENFORCEMENT_ENABLED=true
   ```
3. Run the agent:
   ```bash
   python -m sentinel_agent
   ```

### Laptop 2 (Central Server & SOC Dashboard)
1. Ensure Firewall allows inbound traffic on TCP port `8000` and `5173`.
2. Edit `Laptop 2`'s `.env`:
   ```ini
   CORS_ORIGINS=["http://localhost:5173", "http://<LAPTOP_2_IP>:5173"]
   ```
3. Run the backend binding to all interfaces:
   ```bash
   python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
   ```
4. Run the frontend:
   ```bash
   cd frontend
   npm run dev -- --host 0.0.0.0
   ```
5. View the dashboard on Laptop 2 via `http://localhost:5173`.

---

## 6. Verification and Sanity Testing

Verify the installation by running the automated regression suite:
```bash
# Verify all backend, agent, and policy tests pass:
pytest

# Verify Phase 9 evaluation reproduces:
python -m evaluation.run_all
```
Expected output: **176 passed, 0 failed**.
