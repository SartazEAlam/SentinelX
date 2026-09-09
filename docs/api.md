# SentinelX — API Documentation

> Detailed API documentation will be added in Phase 1 when authentication and resource endpoints are implemented.

## Current Endpoints

### Health Check

```
GET /api/v1/health
```

Returns the current health status of the SentinelX backend.

**Response:**
```json
{
  "status": "ok",
  "service": "sentinelx-backend",
  "version": "0.1.0",
  "database": "healthy",
  "timestamp": "2026-01-01T00:00:00.000000+00:00"
}
```

## Planned Endpoints

| Endpoint | Method | Phase | Description |
|----------|--------|-------|-------------|
| `/api/v1/auth/login` | POST | 1 | User authentication |
| `/api/v1/auth/refresh` | POST | 1 | Token refresh |
| `/api/v1/devices` | GET/POST | 1 | Device management |
| `/api/v1/events` | GET/POST | 1 | Security events |
| `/api/v1/policies` | GET/POST/PUT/DELETE | 4 | Policy management |
| `/api/v1/approvals` | GET/POST | 5 | Approval workflows |
| `/api/v1/alerts` | GET | 4 | Security alerts |
| `/api/v1/statistics` | GET | 6 | Dashboard statistics |

## Interactive Documentation

When the backend is running, full interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
