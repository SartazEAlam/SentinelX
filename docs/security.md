# SentinelX — Security Architecture & Authentication

SentinelX implements a zero-trust model between endpoints, analysts, and backend services.

---

## 1. User Authentication (JWT)

User authentication is stateless and uses signed JSON Web Tokens (**HS256** by default).

### Login Workflow
1. User submits credentials to `POST /api/v1/auth/login`.
2. Backend verifies the password using **bcrypt** with salted hashing.
3. If credentials match and the account is active, an access token is issued with:
   - `sub`: username
   - `role`: user role (`ADMIN`, `SECURITY_ANALYST`, `VIEWER`)
   - `exp`: expiration timestamp (default: 30 minutes)
4. Password changes via `POST /api/v1/auth/change-password` verify the existing password before updating the hash.

---

## 2. Role-Based Access Control (RBAC)

Three discrete roles govern access to API endpoints:

| Resource / Action | VIEWER | SECURITY_ANALYST | ADMIN |
|---|:---:|:---:|:---:|
| **Health Check** | ✅ | ✅ | ✅ |
| **View Dashboard Stats** | ✅ | ✅ | ✅ |
| **View Events & Details** | ✅ | ✅ | ✅ |
| **Submit Approval Request** | ✅ | ✅ | ✅ |
| **View Alerts & Approvals** | ✅ | ✅ | ✅ |
| **View Policies** | ✅ | ✅ | ✅ |
| **Acknowledge / Resolve Alert** | ❌ | ✅ | ✅ |
| **Approve / Reject Approval** | ❌ | ✅ | ✅ |
| **Create Manual Security Alert** | ❌ | ✅ | ✅ |
| **List & Inspect Registered Devices** | ❌ | ✅ | ✅ |
| **Update Device Metadata** | ❌ | ✅ | ✅ |
| **Enable / Disable Device** | ❌ | ✅ | ✅ |
| **Read Audit Logs** | ❌ | ✅ | ✅ |
| **Create / Edit / Delete Policies** | ❌ | ❌ | ✅ |
| **Create / Update / Deactivate Users** | ❌ | ❌ | ✅ |

---

## 3. Endpoint Agent Authentication

Endpoints authenticate independently of users to ensure unattended background agent telemetry cannot impersonate administrative identities.

1. **One-Time Token Issuance**:
   - When an endpoint agent registers via `POST /api/v1/devices/register`, a composite token is generated: `<device_id>.<random_secret>`.
   - The plaintext token is returned **only once** to the agent during registration.
2. **HMAC Storage**:
   - The server only stores the SHA-256 HMAC hash of the token: `token_hash = hmac_sha256(secret_key, token)`.
   - Even if the database is read by an unauthorized party, raw agent tokens cannot be reconstructed.
3. **Deactivation & Revocation**:
   - When a device is disabled (`POST /api/v1/devices/{id}/disable`), `get_current_device` immediately rejects subsequent telemetry with `401 Unauthorized`.

---

## 4. Audit Logging

Every security-sensitive action is captured in the append-only `audit_logs` table:
- User login / failed login attempts
- User account creation, update, and deactivation
- Device registration, heartbeat, enable, and disable
- Security event ingestion (single and batch)
- Approval request creation, approvals, and rejections
- Policy creation, modification, and deletion
- Alert creation, acknowledgment, and resolution

Each audit record logs the timestamp, actor ID (user or device), IP address, resource type, and relevant metadata.
