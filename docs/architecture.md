# SentinelX — Architecture

## System Overview

SentinelX is a multi-component Data Loss Prevention (DLP) system. It follows a client-server architecture where lightweight endpoint agents communicate with a centralized backend that provides policy management, event processing, risk assessment, and an administrative dashboard.

```
┌─────────────────────────────────────────────────────────────┐
│                   Protected Windows Endpoint                │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              SentinelX Endpoint Agent                  │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ File     │  │ Data         │  │ Risk         │   │  │
│  │  │ Monitor  │  │ Classifier   │  │ Assessor     │   │  │
│  │  └────┬─────┘  └──────┬───────┘  └──────┬───────┘   │  │
│  │       │               │                  │           │  │
│  │  ┌────┴───────────────┴──────────────────┴───────┐   │  │
│  │  │            Policy Engine                       │   │  │
│  │  └────────────────────┬───────────────────────────┘   │  │
│  │                       │                               │  │
│  │  ┌────────────────────┴───────────────────────────┐   │  │
│  │  │         Enforcement / Action Layer              │   │  │
│  │  └────────────────────┬───────────────────────────┘   │  │
│  └───────────────────────┼───────────────────────────────┘  │
│                          │ HTTPS / REST                      │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                  SentinelX Central Server                     │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ REST API │  │ Event        │  │ WebSocket /           │   │
│  │ (FastAPI)│  │ Processor    │  │ Realtime Events       │   │
│  └────┬─────┘  └──────┬───────┘  └──────────┬───────────┘   │
│       │               │                      │               │
│  ┌────┴───────────────┴──────────────────────┴───────────┐   │
│  │                   Service Layer                        │   │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐            │   │
│  │  │ Auth    │  │ Policy   │  │ Analytics │            │   │
│  │  │ Service │  │ Service  │  │ Service   │            │   │
│  │  └─────────┘  └──────────┘  └───────────┘            │   │
│  └───────────────────────┬───────────────────────────────┘   │
│                          │                                   │
│  ┌───────────────────────┴───────────────────────────────┐   │
│  │              Database (SQLite / PostgreSQL)             │   │
│  │  Users │ Devices │ Events │ Policies │ Alerts │ Audit  │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│               Administrator Dashboard (React)                │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Event    │  │ Policy   │  │ Device   │  │ Analytics│   │
│  │ Viewer   │  │ Manager  │  │ Manager  │  │ Panel    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Endpoint Agent

The SentinelX agent runs as a native Windows application on protected endpoints. It is responsible for:

- **File Monitoring**: Using `watchdog` to observe file system events (creation, modification, deletion, movement) on protected paths.
- **Data Classification**: Analyzing file content and metadata to determine sensitivity level (Low, Medium, High, Critical).
- **Risk Assessment**: Evaluating operations against risk factors including data sensitivity, destination type, user behavior patterns, and temporal context.
- **Policy Evaluation**: Applying organizational policies to determine the appropriate response to each operation.
- **Enforcement**: Executing policy decisions (allow, log, warn, block, require approval).

The agent communicates with the central server via HTTPS REST API, sending security events and receiving policy updates.

### 2. Central Server (Backend)

The FastAPI-based backend provides:

- **REST API**: Versioned API (`/api/v1/`) for agent communication, dashboard data, and administrative operations.
- **Authentication**: JWT-based authentication for administrators and API token authentication for agents.
- **Event Processing**: Ingestion, storage, and analysis of security events from agents.
- **Policy Management**: CRUD operations for security policies distributed to agents.
- **Realtime Events**: WebSocket connections for live event streaming to the dashboard.

### 3. Database

- **Development**: SQLite for zero-configuration local development.
- **Production**: PostgreSQL for concurrent access, performance, and reliability.
- Uses SQLAlchemy 2.x ORM with Alembic migrations.

**Core Tables** (introduced in later phases):

| Table | Purpose |
|-------|---------|
| `users` | Administrator accounts |
| `devices` | Registered endpoint devices |
| `security_events` | All captured security events |
| `policies` | Security policy definitions |
| `approval_requests` | Pending approval workflows |
| `alerts` | Generated security alerts |
| `audit_log` | System audit trail |

### 4. Dashboard (Frontend)

React + TypeScript single-page application providing:

- Real-time event monitoring
- Policy configuration
- Device management
- Security analytics and reporting
- Approval workflow management
- System health monitoring

### 5. ML Engine (Future)

Machine learning layer for:

- Behavioral anomaly detection
- User risk profiling
- Automated threat classification
- Pattern recognition across events

Uses scikit-learn for model training and inference.

## Data Flow

### Security Event Lifecycle

```
1. File operation detected by agent's file monitor
         │
2. Data classified by sensitivity (Low → Critical)
         │
3. Risk score calculated based on multiple factors
         │
4. Policy evaluated: ALLOW / LOG / WARN / BLOCK / APPROVE
         │
5. Enforcement action taken locally
         │
6. Event transmitted to central server via REST API
         │
7. Event stored in database
         │
8. Dashboard updated via WebSocket
         │
9. Alert generated if risk threshold exceeded
```

## Security Considerations

- All agent-server communication over HTTPS
- JWT authentication for administrators
- API token authentication for agents
- No secrets in source code or logs
- Parameterized database queries via SQLAlchemy ORM
- CORS configured per environment
- Input validation via Pydantic schemas
- Audit logging for all administrative actions

## Deployment Model

- **Development**: SQLite + local Python + Vite dev server
- **Staging/Production**: PostgreSQL via Docker Compose + containerized backend
- **Agent**: Native Windows installation (not containerized)
