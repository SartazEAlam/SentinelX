# SentinelX — Database Documentation

SentinelX utilizes an asynchronous/synchronous database architecture powered by **SQLAlchemy 2.x ORM** and **Alembic** migrations. It supports both **SQLite** (default for local development and unit tests) and **PostgreSQL** (for production / containerized deployments).

---

## Entity Relationship Overview

SentinelX models 7 core domain entities:

```mermaid
erDiagram
    USERS ||--o{ POLICIES : "creates"
    USERS ||--o{ APPROVAL_REQUESTS : "requests"
    USERS ||--o{ APPROVAL_REQUESTS : "reviews"
    USERS ||--o{ ALERTS : "acknowledges/resolves"
    USERS ||--o{ AUDIT_LOGS : "performs"
    DEVICES ||--o{ SECURITY_EVENTS : "generates"
    DEVICES ||--o{ ALERTS : "associated_with"
    DEVICES ||--o{ AUDIT_LOGS : "originates"
    SECURITY_EVENTS ||--o{ APPROVAL_REQUESTS : "subject_of"
    SECURITY_EVENTS ||--o{ ALERTS : "triggers"

    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string full_name
        string role "ADMIN | SECURITY_ANALYST | VIEWER"
        boolean is_active
        datetime last_login_at
        datetime created_at
        datetime updated_at
    }

    DEVICES {
        int id PK
        string device_id UK
        string device_name
        string hostname
        string operating_system
        string os_version
        string agent_version
        string ip_address
        string status "ONLINE | OFFLINE | UNKNOWN | DISABLED"
        datetime last_seen_at
        datetime registered_at
        datetime updated_at
        boolean is_active
        string token_hash
    }

    SECURITY_EVENTS {
        int id PK
        string event_id UK
        string device_id FK
        datetime timestamp
        string event_type
        string action
        string source
        string destination
        string file_name
        string file_path
        int file_size
        string file_hash
        string sensitivity_level
        float risk_score
        string decision "ALLOW | HOLD | BLOCK | MONITOR"
        string status
        string user_context
        string process_name
        int process_id
        text metadata_json
        datetime created_at
    }

    POLICIES {
        int id PK
        string name UK
        string description
        boolean enabled
        int priority
        text sensitivity_levels
        float risk_threshold
        text allowed_actions
        string decision
        text conditions
        int created_by FK
        datetime created_at
        datetime updated_at
    }

    ALERTS {
        int id PK
        string alert_id UK
        int event_id FK
        string device_id FK
        string severity "LOW | MEDIUM | HIGH | CRITICAL"
        string title
        text message
        string status "OPEN | ACKNOWLEDGED | RESOLVED"
        datetime created_at
        datetime acknowledged_at
        int acknowledged_by FK
        datetime resolved_at
        int resolved_by FK
    }

    APPROVAL_REQUESTS {
        int id PK
        string request_id UK
        int event_id FK
        int requested_by FK
        int assigned_to FK
        string status "PENDING | APPROVED | REJECTED | EXPIRED | CANCELLED"
        text reason
        text reviewer_comment
        datetime created_at
        datetime reviewed_at
    }

    AUDIT_LOGS {
        int id PK
        int actor_user_id FK
        string actor_device_id
        string action
        string resource_type
        string resource_id
        datetime timestamp
        string ip_address
        string user_agent
        text metadata_json
    }
```

---

## Alembic Migration Workflow

Database schema evolution is managed via Alembic located under `backend/alembic/`.

### Migration Commands

Run migrations from the `backend/` directory:

```bash
# Upgrade database to latest revision
alembic upgrade head

# Rollback one revision
alembic downgrade -1

# Rollback to beginning
alembic downgrade base

# Create a new migration after model changes
alembic revision --autogenerate -m "describe changes"
```

### Seeding Development Data

To populate your database with realistic sample devices, policies, events, and alerts:

```bash
# From project root
python scripts/seed_dev.py
```
