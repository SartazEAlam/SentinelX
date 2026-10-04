# SentinelX Two-Laptop Deployment Setup

This document describes the process for deploying SentinelX in a physically isolated, two-laptop configuration for true end-to-end validation.

## Architecture

```text
                 LAPTOP 1
            PROTECTED ENDPOINT
                    │
                    │
            SentinelX Agent
                    │
                    ├── Monitoring
                    ├── Classification
                    ├── Risk
                    ├── Policy
                    └── Enforcement
                    │
                    │ Authenticated Network (HTTP/REST)
                    ▼
                 LAPTOP 2
          CENTRAL SENTINELX SERVER
                    │
          ┌─────────┼─────────┐
          │         │         │
          ▼         ▼         ▼
       FastAPI   Database   Realtime
          │                   │
          │                   ▼
          │             Administrator
          │               Dashboard
          │
          └──── Approval / Audit
```

## Laptop 2 Configuration (Central Server & Dashboard)

This laptop acts as the central SOC and data processing backend. It must be accessible over the LAN by Laptop 1.

### 1. Network Interface
Determine Laptop 2's LAN IP address (e.g., `192.168.1.50`).

### 2. Backend Environment (`backend/.env` or Project Root `.env`)
Configure the backend to listen on all interfaces so Laptop 1 can reach it:
```ini
ENVIRONMENT=testing
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DATABASE_URL=sqlite:///./sentinelx.db
JWT_SECRET_KEY=STRONG_SECURE_KEY_123!
```

### 3. Start Backend
Run the backend server on Laptop 2:
```bash
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

### 4. Start Dashboard
Run the frontend dashboard on Laptop 2:
```bash
cd frontend
npm run dev -- --host
```
You can access the dashboard at `http://localhost:5173`.

---

## Laptop 1 Configuration (Protected Endpoint)

This laptop represents the employee workstation monitored by SentinelX.

### 1. Agent Environment (`.env` or Exported Variables)
Configure the agent to communicate with Laptop 2's IP address:
```ini
AGENT_SERVER_URL=http://192.168.1.50:8000
AGENT_DEVICE_ID=laptop-001-test
AGENT_API_TOKEN=VALID_BACKEND_TOKEN
AGENT_HEARTBEAT_INTERVAL_SECONDS=10
AGENT_ENFORCEMENT_ENABLED=true
AGENT_MONITORING_MODE=STRICT
```

### 2. Run the Agent
Execute the agent on Laptop 1:
```bash
python -m sentinel_agent
```

### 3. Verify Connectivity
- Check the console on Laptop 1 for successful registration (`200 OK`).
- Check the console on Laptop 2 (Backend) for incoming `/api/v1/devices/register` and `/api/v1/devices/heartbeat` requests.
- Open the Dashboard on Laptop 2 and navigate to **Devices**. You should see `laptop-001-test` listed as online.
