# SentinelX: Repeatable Live Demonstration Script

**Document Version:** 1.0.0 (Final Delivery)  
**Target Audience:** Final-Year Viva Examiners, Technical Evaluators, Demonstration Presenters  

---

## 1. Demonstration Environment Setup

Ensure the virtual environment is activated and dependencies are installed. Prepare 4 terminal windows:

| Terminal | Purpose | Command |
| :---: | :--- | :--- |
| **Terminal 1** | FastAPI Backend Server | `python -m uvicorn app.main:app --app-dir backend --reload --port 8000` |
| **Terminal 2** | SOC Administrator Dashboard | `cd frontend && npm run dev` |
| **Terminal 3** | SentinelX Endpoint Agent | `python -m sentinel_agent` |
| **Terminal 4** | Demonstration Commands | Interactive shell for generating test file actions |

---

## 2. Step-by-Step 12-Stage Demonstration Sequence

---

### Stage 1: Start Backend & Initialize Database
- **Command:** `python -m uvicorn app.main:app --app-dir backend --reload --port 8000`
- **Expected Output:**
  ```text
  INFO: Started server process
  INFO: Database initialized - ./sentinelx.db
  INFO: Application startup complete. Uvicorn running on http://127.0.0.1:8000
  ```
- **Verification:** Visit `http://localhost:8000/docs` to show Swagger API documentation.

---

### Stage 2: Launch SOC Administrator Dashboard
- **Command:** `cd frontend && npm run dev`
- **Dashboard URL:** `http://localhost:5173`
- **Action:** Log in with `admin` / `Admin@123!`.
- **Expected Appearance:**
  - Navigation bar displaying: Overview, Events, Approvals, Alerts, Policies, Devices, Audit.
  - Telemetry cards showing 0 or seeded events, connection status "Connected" via WebSocket.

---

### Stage 3: Launch Protected Endpoint Agent
- **Command:** `python -m sentinel_agent`
- **Expected Terminal Output:**
  ```text
  +------------------------------------------+
  |         SentinelX Endpoint Agent         |
  |              v3.0.0                      |
  +------------------------------------------+
  Device     : dev-xxxx-xxxx
  Mode       : STRICT
  Server     : http://localhost:8000
  Started    : 2026-10-09 ...
  ```

---

### Stage 4: Verify Device Registration & Fleet Telemetry
- **Dashboard Action:** Navigate to **Devices** (`/devices`).
- **Verification:** The newly started device appears with status **ONLINE**, Windows OS, trust score (95%), and active heartbeat timestamp.

---

### Stage 5: Demonstrate Normal Operation (Outcome: ALLOW)
- **Concept:** Low-risk operation involving non-sensitive internal documentation.
- **Command (Terminal 4):**
  ```powershell
  New-Item -ItemType Directory -Force -Path "C:/tmp/sentinelx_protected"
  Set-Content -Path "C:/tmp/sentinelx_protected/weekly_sync.txt" -Value "Meeting notes: Team completed sprint planning. Engineering design review scheduled for Thursday at 10 AM."
  ```
- **Expected Behavior:**
  - Agent classifies content as `PUBLIC` (Confidence: 0.90).
  - Risk Engine calculates score: ~`4.68` (`LOW`).
  - Policy Engine returns decision: **`ALLOW`**.
  - File remains untouched in `C:/tmp/sentinelx_protected/weekly_sync.txt`.
- **Dashboard Verification:** In **Events** (`/events`), view the event with Decision `ALLOW` in green badge.

---

### Stage 6: Demonstrate Warning-Level Operation (Outcome: HOLD)
- **Concept:** Medium-risk operation involving confidential internal payroll data copied to a simulated removable media folder.
- **Command (Terminal 4):**
  ```powershell
  Set-Content -Path "C:/tmp/sentinelx_protected/q3_salary_data.csv" -Value "employee_id,name,role,salary`nEMP0102,Alice Smith,Principal Engineer,185000`nEMP0103,Bob Jones,Director,210000"
  ```
- **Expected Behavior:**
  - Agent classifies content as `CONFIDENTIAL` (Categories: `EMPLOYEE_DATA`).
  - Risk Engine calculates score: ~`38.01` (`MEDIUM`).
  - Policy Engine returns decision: **`HOLD`**.
  - File is moved to local quarantine staging folder `C:/tmp/sentinelx_staging/` awaiting administrative approval.

---

### Stage 7: SOC Approval of Quarantined Operation
- **Dashboard Action:**
  1. Navigate to **Approvals** (`/approvals`).
  2. A new pending request appears for `q3_salary_data.csv`.
  3. Click **Approve**. Enter comment: *"Approved for Q3 compensation audit"*.
- **Expected Outcome:**
  - Backend updates status to `APPROVED`.
  - Endpoint agent receives approval notification and releases the file from staging to destination.
  - Audit log records the approval decision.

---

### Stage 8: Demonstrate Quarantined Operation Denied (Outcome: DENY)
- **Command (Terminal 4):**
  ```powershell
  Set-Content -Path "C:/tmp/sentinelx_protected/customer_contacts_export.csv" -Value "customer_id,full_name,email,phone`nCUST9901,John Doe,jdoe@corp.com,+1-555-0199`nCUST9902,Jane Roe,jroe@corp.com,+1-555-0188"
  ```
- **Dashboard Action:**
  1. The event enters **HOLD** state and appears in the approval queue.
  2. Click **Reject**. Enter comment: *"Unauthorized external customer data export"*.
- **Expected Outcome:**
  - Backend sets status to `REJECTED`.
  - Agent permanently deletes the quarantined file from staging.
  - Operation remains prevented.

---

### Stage 9: Demonstrate High-Risk Exfiltration Blocked (Outcome: BLOCK)
- **Concept:** Prohibited high-risk credential leak (.env passwords / cloud secret keys).
- **Command (Terminal 4):**
  ```powershell
  Set-Content -Path "C:/tmp/sentinelx_protected/production_credentials.env" -Value "DATABASE_URL=postgres://admin:SuperSecretRootPassword992@prod-db.internal:5432/main`nAPI_SECRET=mock_api_secret_key_token_9901_simulated"
  ```
- **Expected Behavior:**
  - Agent detects credentials and secret tokens (`HIGHLY_CONFIDENTIAL`).
  - Risk Engine calculates score: $\ge \mathbf{70.0}$ (`HIGH`).
  - Policy Engine triggers: **`BLOCK`**.
  - BlockHandler immediately purges `production_credentials.env` from the folder.
  - File disappears within milliseconds.
- **Dashboard Verification:**
  - Event appears in **Events** with red `BLOCK` badge.
  - A critical incident alert is posted to **Alerts** (`/alerts`) titled *"Blocked High-Risk Exfiltration Attempt"*.

---

### Stage 10: Inspect Audit Trail & Event Details
- **Dashboard Action:**
  - Click on the blocked event in `/events` to show factor contributions (Sensitivity: 30%, Action: 20%, Destination: 20%).
  - Navigate to **Audit Logs** (`/audit`) to demonstrate immutable records of every user login, policy evaluation, approval decision, and system modification.

---

### Stage 11: Present Live Phase 9 Evaluation Results
- **Command (Terminal 4):**
  ```bash
  python -m evaluation.run_all
  ```
- **Expected Output:**
  - Executes full benchmark across 180 unseen test samples.
  - Prints final comparison table:
    - **Rule-Based:** Accuracy: 78.33%, Precision: 71.43%, Recall: 94.44%, Latency: 0.024 ms
    - **Logistic Regression:** Accuracy: 100.00%, Precision: 100.00%, Recall: 100.00%, Latency: 0.017 ms
    - **Random Forest:** Accuracy: 100.00%, Precision: 100.00%, Recall: 100.00%, Latency: 0.167 ms
    - **SentinelX Hybrid:** Accuracy: 81.67%, Precision: 77.67%, Recall: 88.89%, Latency: 33.613 ms
  - End-to-end latency breakdown: Mean = 54.98 ms (P95 = 59.87 ms).
  - Endpoint resource usage: 0.0% idle CPU, zero memory leaks (<0.4 MB delta).

---

### Stage 12: Showcase Evaluation Figures & Charts
- **Action:** Open and present generated charts in `docs/evaluation/`:
  - `confusion_matrix_hybrid.png` (80 TP, 67 TN, 23 FP, 10 FN)
  - `model_metrics_comparison.png` (Bar chart comparing Accuracy, Precision, Recall, F1)
  - `latency_comparison.png` (Sub-millisecond inference vs end-to-end stage breakdown)
  - `roc_pr_curves.png` (ROC-AUC = 0.9319 for Hybrid model)
  - `resource_usage.png` (Memory RSS progression and disk footprints)
