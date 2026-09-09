# SentinelX — Testing Strategy

> Comprehensive testing will be expanded in Phase 9.

## Current Tests (Phase 0)

### Backend
- Health endpoint returns HTTP 200
- Health endpoint response structure validation
- Configuration loading with defaults
- Configuration validation (log levels, environment)

### Agent
- Agent configuration validation
- Agent lifecycle (start/stop)

### Frontend
- Build verification

## Planned Test Areas

| Area | Phase | Description |
|------|-------|-------------|
| Authentication | 1 | Login, token refresh, authorization |
| Event ingestion | 2 | Event creation, validation, storage |
| Classification | 3 | Sensitivity level assignment |
| Policy engine | 4 | Policy evaluation, action determination |
| Enforcement | 5 | File blocking, USB control |
| End-to-end | 7 | Agent → Backend → Dashboard |
| ML models | 8 | Model accuracy, false positive rates |
