# SentinelX: Operational Troubleshooting Guide

**Document Version:** 1.0.0 (Final Delivery)  
**Target Audience:** Administrators, Demonstrators, Evaluators  

---

## 1. Common Startup & Runtime Issues

### 1.1 Backend: "Address already in use: Port 8000"
- **Cause:** A previous instance of Uvicorn or another service is already bound to port 8000.
- **Remediation:**
  ```powershell
  # Find process occupying port 8000:
  netstat -ano | findstr :8000
  # Terminate the process (replace PID with actual process ID):
  taskkill /PID <PID> /F
  ```
  Then restart the server:
  ```bash
  python -m uvicorn app.main:app --app-dir backend --reload --port 8000
  ```

### 1.2 Frontend: WebSocket Disconnected / Live Feed Paused
- **Cause:** Backend server is not running or CORS origins in `.env` do not match the browser's address.
- **Remediation:**
  1. Ensure the backend is running and healthy (`http://localhost:8000/api/v1/health`).
  2. Inspect `.env` on the backend host and verify `CORS_ORIGINS` includes your dashboard URL:
     ```ini
     CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
     ```

### 1.3 Agent: "Failed to register with backend (Connection Refused)"
- **Cause:** Endpoint agent started before the backend was online, or `AGENT_SERVER_URL` is pointing to an incorrect IP.
- **Remediation:**
  1. Verify the backend is accessible from the agent terminal:
     ```bash
     curl http://localhost:8000/api/v1/health
     ```
  2. In `.env`, ensure `AGENT_SERVER_URL=http://localhost:8000` (or the server host IP for two-laptop setups).

### 1.4 Agent: "Permission Denied: agent/staging"
- **Cause:** Windows user lacks write permissions to the staging folder or the directory was locked by another process.
- **Remediation:**
  Ensure the staging path configured in `.env` exists and is writable:
  ```powershell
  New-Item -ItemType Directory -Force -Path "C:/tmp/sentinelx_staging"
  ```

---

## 2. Two-Laptop Network Troubleshooting

### 2.1 Agent on Laptop 1 Cannot Connect to Backend on Laptop 2
- **Diagnosis Checklist:**
  1. **Ping Connectivity:** On Laptop 1, run `ping <LAPTOP_2_IP>`. If requests time out, verify both laptops are on the same Wi-Fi network and AP Isolation is disabled.
  2. **Windows Firewall:** On Laptop 2 (Server), Windows Firewall often blocks incoming connections on non-standard ports. Allow port 8000:
     ```powershell
     # In Admin PowerShell on Laptop 2:
     New-NetFirewallRule -DisplayName "SentinelX Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
     ```
  3. **Host Binding:** Ensure Uvicorn on Laptop 2 is bound to `0.0.0.0` (all interfaces), not `127.0.0.1`:
     ```bash
     python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
     ```

---

## 3. Database & Authentication Diagnostics

### 3.1 "Invalid Credentials" on Dashboard Login
- **Remediation:**
  Re-seed the initial admin and analyst credentials:
  ```bash
  python scripts/seed_dev.py
  ```
  Default logins:
  - Admin: `admin` / `Admin@123!`
  - Analyst: `analyst` / `Analyst@123!`

### 3.2 Database Migration / Schema Out of Sync
- **Remediation:**
  The SQLite database automatically initializes all models on startup. For a clean reset during development:
  ```bash
  rm backend/sentinelx.db
  python scripts/seed_dev.py
  ```
