# SentinelX: Administrator and SOC Analyst Manual

**Document Version:** 1.0.0 (Final Delivery)  
**Target Audience:** Security Operations Center (SOC) Analysts, IT Administrators, CISOs  

---

## 1. Accessing the SOC Dashboard

1. Navigate to `http://localhost:5173` (or the corporate host IP over HTTPS in production).
2. Default Administrative Credentials (seeded via `scripts/seed_dev.py`):
   - **Administrator:** Username: `admin` | Password: `Admin@123!`
   - **Security Analyst:** Username: `analyst` | Password: `Analyst@123!`

---

## 2. Role-Based Access Control (RBAC)

SentinelX enforces three distinct administrative privilege tiers:

| Role | Permissions |
| :--- | :--- |
| **ADMIN** | Full administrative control: user creation, policy modification, approval reviews, alert resolution, device deregistration, audit log viewing. |
| **ANALYST** | Operational security management: viewing events, reviewing and acting on approvals, acknowledging and resolving alerts, viewing devices. |
| **VIEWER** | Read-only telemetry: inspecting events and dashboard graphs. Cannot modify policies or make approval decisions. |

---

## 3. Dashboard Navigation & Modules

### 3.1 Overview (Dashboard Home)
- **Top Metrics:** Total Events Ingested, Active Connected Endpoints, High-Risk Security Incidents, Pending Approvals.
- **Visual Analytics (Recharts):**
  - Event Distribution by Sensitivity Level (PUBLIC, INTERNAL, CONFIDENTIAL, HIGHLY_CONFIDENTIAL).
  - Risk Score Histogram across monitored operations.
  - Live Real-Time Event Stream via WebSocket connection.

### 3.2 Events Explorer (`/events`)
- Lists all normalized endpoint events.
- **Search & Filter:**
  - Search by filename or device identifier.
  - Filter by Decision (`ALLOW`, `HOLD`, `BLOCK`).
  - Filter by Sensitivity Level or minimum risk score.
- **Detailed Event View (`/events/:id`):**
  - Displays SHA-256 file hash, path, process ID.
  - Factor contribution breakdown from the 8-factor Risk Engine.
  - Matched classification evidence (e.g., regex patterns, keyword triggers).

### 3.3 Approval Workflow (`/approvals`)
- Central queue for operations placed in `HOLD` quarantine.
- **Reviewing a Request:**
  1. Inspect the file name, requesting user, source path, destination, and calculated risk score.
  2. Click **Approve** to authorize the operation (requires optional justification comment). The agent immediately releases the file from quarantine to the destination.
  3. Click **Reject** to deny the operation. The agent immediately deletes the staged copy.

### 3.4 Alerts & Incident Center (`/alerts`)
- Surfaces critical and high-severity DLP violations (e.g., blocked bulk card exfiltration or credentials upload).
- **Incident Lifecycle:**
  - `OPEN` $\to$ Analyst clicks **Acknowledge** (records investigating analyst).
  - `ACKNOWLEDGED` $\to$ Analyst clicks **Resolve** (inputs resolution justification).
  - `RESOLVED` $\to$ Closes incident and writes immutable audit record.

### 3.5 Policy Engine Configuration (`/policies`)
- Manage active DLP enforcement rules.
- **Rule Attributes:**
  - **Priority (1-100):** Higher priority rules evaluate first.
  - **Decision:** `ALLOW`, `HOLD`, `BLOCK`.
  - **Risk Thresholds:** Minimum and maximum score bands (e.g., Min: 70 $\implies$ BLOCK).
  - **Toggle Enable/Disable:** Instant policy updates without restarting endpoints.

### 3.6 Device Fleet Manager (`/devices`)
- Monitors endpoint agent health.
- Shows hostname, IP address, OS version, agent version, trust score, and heartbeat status (`ONLINE`, `DEGRADED`, `OFFLINE`).

### 3.7 Audit Log Inspector (`/audit`)
- Provides immutable audit trails for regulatory compliance (GDPR, HIPAA, PCI-DSS).
- Records who performed what administrative action, when, and from what IP address.
