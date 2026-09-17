# SentinelX — API Reference

The SentinelX REST API is built with FastAPI. When the server is running, interactive API documentation and testing interfaces are available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

All endpoints are prefixed with `/api/v1`.

---

## Authentication Schemes

The SentinelX API uses two distinct Bearer token authentication schemes:

1. **User JWT (`Authorization: Bearer <jwt_token>`)**
   - Returned by `POST /api/v1/auth/login`.
   - Encodes user identity (`sub`), assigned role (`ADMIN`, `SECURITY_ANALYST`, `VIEWER`), and expiration (`exp`).
   - Required for administrative, dashboard, analyst, and audit endpoints.

2. **Device Token (`Authorization: Bearer <device_id>.<secret>`)**
   - Issued once during endpoint registration (`POST /api/v1/devices/register`).
   - Stored in hashed format (HMAC SHA-256) on the backend.
   - Required for agent telemetry: `POST /api/v1/devices/heartbeat`, `POST /api/v1/events`, `POST /api/v1/events/batch`.

---

## Error Handling

All non-2xx responses follow a standardized error envelope:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource with specified identifier was not found."
  }
}
```

| HTTP Status | Code | Description |
|---|---|---|
| `400 Bad Request` | `BAD_REQUEST` | Malformed input or unparseable payload |
| `401 Unauthorized` | `UNAUTHORIZED` | Missing or invalid user/device token |
| `403 Forbidden` | `FORBIDDEN` | Insufficient role permissions |
| `404 Not Found` | `NOT_FOUND` | Target resource does not exist |
| `409 Conflict` | `CONFLICT` | Resource already exists, batch limit exceeded, or device disabled |
| `422 Unprocessable Entity` | Validation | Pydantic schema validation error |
| `500 Internal Error` | `INTERNAL_ERROR` | Unexpected server exception |

---

## Endpoints Summary

### 1. Health & System
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/health` | Public | System status, database health, version |

### 2. Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Public | Authenticate user & receive JWT access token |
| `GET` | `/api/v1/auth/me` | User | Get current logged-in user details |
| `POST` | `/api/v1/auth/change-password` | User | Update password (requires current password verification) |

### 3. User Management
| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/users` | ADMIN | List paginated users |
| `POST` | `/api/v1/users` | ADMIN | Create new user (ADMIN, SECURITY_ANALYST, VIEWER) |
| `GET` | `/api/v1/users/{user_id}` | ADMIN | Get user details by ID |
| `PATCH` | `/api/v1/users/{user_id}` | ADMIN | Update user attributes or role |
| `DELETE` | `/api/v1/users/{user_id}` | ADMIN | Soft-deactivate user account |

### 4. Device Management
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/devices/register` | Public / Agent | Register endpoint & receive one-time authentication token |
| `POST` | `/api/v1/devices/heartbeat` | Device Token | Report agent status & update `last_seen_at` |
| `GET` | `/api/v1/devices` | ANALYST / ADMIN | List registered endpoints with optional status filtering |
| `GET` | `/api/v1/devices/{device_id}` | ANALYST / ADMIN | Get device details |
| `PATCH` | `/api/v1/devices/{device_id}` | ANALYST / ADMIN | Update device metadata |
| `POST` | `/api/v1/devices/{device_id}/enable` | ANALYST / ADMIN | Re-enable a disabled endpoint |
| `POST` | `/api/v1/devices/{device_id}/disable` | ANALYST / ADMIN | Disable an active endpoint |

### 5. Security Events
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/events` | Device Token | Ingest a single security event from endpoint |
| `POST` | `/api/v1/events/batch` | Device Token | Ingest batch of events (max 100 per request) |
| `GET` | `/api/v1/events` | VIEWER / ANALYST / ADMIN | List events with filtering (device, type, sensitivity, risk, decision, dates) |
| `GET` | `/api/v1/events/{event_id}` | VIEWER / ANALYST / ADMIN | Retrieve a single security event |

### 6. Policy Management
| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/policies` | VIEWER / ANALYST / ADMIN | List DLP policies |
| `POST` | `/api/v1/policies` | ADMIN | Create a new DLP rule |
| `GET` | `/api/v1/policies/{policy_id}` | VIEWER / ANALYST / ADMIN | Get policy details |
| `PATCH` | `/api/v1/policies/{policy_id}` | ADMIN | Update policy rules, conditions, or priority |
| `DELETE` | `/api/v1/policies/{policy_id}` | ADMIN | Delete a DLP rule |

### 7. Security Alerts
| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/alerts` | VIEWER / ANALYST / ADMIN | List security alerts (filter by status, severity, device) |
| `POST` | `/api/v1/alerts` | ANALYST / ADMIN | Create a manual security alert |
| `GET` | `/api/v1/alerts/{alert_id}` | VIEWER / ANALYST / ADMIN | Get alert details |
| `POST` | `/api/v1/alerts/{alert_id}/acknowledge` | ANALYST / ADMIN | Acknowledge open alert with notes |
| `POST` | `/api/v1/alerts/{alert_id}/resolve` | ANALYST / ADMIN | Resolve alert with remediation notes |

### 8. Approval Workflows
| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/approvals` | VIEWER / ANALYST / ADMIN | List pending/reviewed approval requests |
| `POST` | `/api/v1/approvals` | VIEWER / ANALYST / ADMIN | Submit an approval request for an event |
| `GET` | `/api/v1/approvals/{approval_id}` | VIEWER / ANALYST / ADMIN | Get approval request details |
| `POST` | `/api/v1/approvals/{approval_id}/approve` | ANALYST / ADMIN | Approve a pending request |
| `POST` | `/api/v1/approvals/{approval_id}/reject` | ANALYST / ADMIN | Reject a pending request |

### 9. Audit Logging & Dashboard Stats
| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/audit-logs` | ANALYST / ADMIN | Append-only audit log query with actor and action filters |
| `GET` | `/api/v1/stats/overview` | VIEWER / ANALYST / ADMIN | High-level metrics (events count, alerts by severity, device statuses) |
