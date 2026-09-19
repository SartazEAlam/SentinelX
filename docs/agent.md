# SentinelX Endpoint Agent — Architecture & Operations Guide

## Overview

The SentinelX Endpoint Agent is a lightweight, modular Python application that runs on a protected endpoint (laptop, workstation, or server) and monitors file system activity, removable media, and process context. Detected events are normalised, deduplicated, and transmitted to the SentinelX central server for analysis.

The agent operates in **detect-only** mode — it observes and reports activity but does **not** block, quarantine, or prevent any actions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SentinelX Endpoint Agent                  │
│                                                             │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐           │
│  │ FS Coll.  │  │ USB Coll. │  │ Process Ctx. │           │
│  │(watchdog) │  │ (psutil)  │  │  (psutil)    │           │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘           │
│        │               │               │                    │
│        └───────────┬───┘───────────────┘                    │
│                    ▼                                        │
│            ┌───────────────┐                                │
│            │  Normalizer   │                                │
│            └───────┬───────┘                                │
│                    ▼                                        │
│            ┌───────────────┐                                │
│            │ Deduplicator  │                                │
│            └───────┬───────┘                                │
│                    ▼                                        │
│            ┌───────────────┐     ┌──────────────┐          │
│            │  Event Queue  │────▶│  Dispatcher   │          │
│            └───────────────┘     └──────┬───────┘          │
│                                         │                   │
│                    ┌────────────────────┤                   │
│                    ▼                    ▼                   │
│          ┌──────────────┐    ┌──────────────────┐          │
│          │ Local Store  │    │  HTTP Transport   │          │
│          │  (SQLite)    │◀──▶│  (httpx → REST)  │          │
│          └──────────────┘    └────────┬─────────┘          │
│                                       │                     │
└───────────────────────────────────────┼─────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  SentinelX Server │
                              │  (Phase 1 API)   │
                              └──────────────────┘
```

## Agent State Machine

```
INITIALIZING → REGISTERING → RUNNING ⇄ DEGRADED → STOPPING → STOPPED
```

| State | Description |
|-------|-------------|
| `INITIALIZING` | Loading identity, creating transport and pipeline components |
| `REGISTERING` | First-time device registration with the backend |
| `RUNNING` | All systems operational, events being sent to server |
| `DEGRADED` | Server unreachable — monitoring continues, events stored locally |
| `STOPPING` | Graceful shutdown in progress — flushing remaining events |
| `STOPPED` | Agent fully shut down |

## Modules

### Identity (`identity.py`)
- Generates a UUID-based device identity on first run
- Stores device_id, hostname, OS metadata, and auth token in `~/.sentinelx/identity.json`
- On subsequent runs, reuses the existing identity

### Transport (`transport/http_transport.py`)
- Async HTTP client using `httpx` with connection pooling
- Communicates with backend API: registration, heartbeat, single/batch events
- Configurable retry with exponential backoff (default: 3 retries, 5s base)
- 4xx errors are not retried; 5xx and network errors are

### Local Event Store (`storage/event_store.py`)
- SQLite database at `~/.sentinelx/event_store.db`
- Persists events that fail to transmit (offline resilience)
- Events are marked PENDING → SENT or FAILED
- Dispatcher periodically retries PENDING events when connectivity returns

### Event Pipeline (`pipeline/`)
- **`models.py`**: `EndpointEvent` — the agent's canonical normalised event format
- **`normalizer.py`**: Converts raw OS events (FS, USB, process) into EndpointEvent, enriches with file size/hash/user context
- **`deduplicator.py`**: LRU cache with TTL (2s default) to suppress rapid-fire duplicate events from watchdog
- **`queue.py`**: Bounded async queue (5000 max) bridging collectors and dispatcher
- **`dispatcher.py`**: Background task that drains the queue, batches events, and sends to the backend

### Collectors (`monitoring/`)
- **`filesystem.py`**: Uses `watchdog` to observe file creates, modifies, deletes, and moves in configured paths
- **`usb.py`**: Polls `psutil.disk_partitions()` every 5 seconds to detect removable media insertion/removal
- **`process_context.py`**: LRU-cached `psutil.Process()` lookups for enriching events with process metadata

---

## Configuration Reference

All settings are loaded from environment variables prefixed with `AGENT_`. They can also be set in the `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_SERVER_URL` | `http://localhost:8000` | Backend server URL |
| `AGENT_DEVICE_ID` | `dev-endpoint-001` | Device identifier (overridden by identity manager) |
| `AGENT_API_TOKEN` | `CHANGE_ME` | Auth token (overridden after registration) |
| `AGENT_LOG_LEVEL` | `INFO` | Logging level |
| `AGENT_MONITORING_MODE` | `MONITOR_ONLY` | Monitoring strictness mode |
| `AGENT_PROTECTED_PATHS` | *(empty)* | Comma-separated paths to monitor |
| `AGENT_TRUSTED_PATHS` | *(empty)* | Comma-separated trusted paths |
| `AGENT_HEARTBEAT_INTERVAL_SECONDS` | `60` | Seconds between heartbeats |
| `AGENT_BATCH_SIZE` | `50` | Max events per batch |
| `AGENT_BATCH_FLUSH_INTERVAL_SECONDS` | `10` | Seconds between batch flushes |
| `AGENT_IDENTITY_DIR` | `~/.sentinelx` | Directory for identity and local store |
| `AGENT_MAX_RETRY_ATTEMPTS` | `3` | HTTP retry attempts |
| `AGENT_RETRY_BACKOFF_SECONDS` | `5` | Base backoff between retries |
| `AGENT_FILE_HASH_ENABLED` | `true` | Enable SHA-256 file hashing |
| `AGENT_FILE_HASH_MAX_SIZE_MB` | `50` | Max file size (MB) to hash |
| `AGENT_EXCLUDED_EXTENSIONS` | `.tmp,.log,.lock,.swp,.swo` | Extensions to ignore |
| `AGENT_EXCLUDED_DIRECTORIES` | `.git,.venv,node_modules,...` | Directories to ignore |
| `AGENT_USB_POLL_INTERVAL_SECONDS` | `5` | USB detection poll interval |

---

## Security Model

### Device Identity
- On first run, the agent generates a UUID-based `device_id` and registers with the backend
- The backend returns a one-time plaintext token
- The token is stored in `~/.sentinelx/identity.json` (plaintext on disk)
- **Known limitation**: Production deployments should use OS keyring or TPM-backed storage

### Communication
- All API calls use `Authorization: Bearer <device_token>`
- Communication uses HTTP (configurable to HTTPS for production)
- Token is never logged in plaintext

### Data Flow
- Events contain file metadata (path, name, size, SHA-256 hash) but **never** file contents
- No sensitive data classification or content inspection in Phase 2

---

## Running the Agent

### Quick Start (same machine as server)
```bash
# 1. Start the backend
cd d:\SentinelX\backend
uvicorn app.main:app --reload

# 2. Configure and run the agent
cd d:\SentinelX\agent
# Edit .env to set AGENT_PROTECTED_PATHS
python -m sentinel_agent
```

### Two-Laptop Deployment
```bash
# On the server machine:
cd d:\SentinelX\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# On the endpoint machine:
# Set AGENT_SERVER_URL to the server's IP
AGENT_SERVER_URL=http://192.168.1.100:8000
AGENT_PROTECTED_PATHS=C:\Users\user\Documents,D:\sensitive
python -m sentinel_agent
```

### Verifying Operation
1. Check the agent startup banner for device ID and state
2. Monitor backend logs for registration and heartbeat
3. Check `GET /api/v1/devices` for the registered device
4. Create/modify files in monitored paths
5. Check `GET /api/v1/events` for ingested events

---

## Offline Behaviour

When the server is unreachable:
1. Agent transitions to `DEGRADED` state
2. Collectors continue monitoring normally
3. Events are queued in memory and overflow to the local SQLite store
4. Heartbeats fail silently with warnings
5. Every ~60 seconds, the dispatcher retries sending from the local store
6. When connectivity returns, queued events drain to the server
7. Agent transitions back to `RUNNING` state
