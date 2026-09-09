# SentinelX — Known Limitations

## Phase 0 Limitations

- **No authentication**: All API endpoints are publicly accessible
- **No encryption**: Agent-server communication is unencrypted HTTP
- **No enforcement**: The agent observes but does not block any operations
- **No real monitoring**: File system and USB monitoring are not yet implemented
- **No ML models**: Behavioral analytics and anomaly detection are not trained
- **SQLite only**: Production-grade database (PostgreSQL) requires Docker setup
- **Single endpoint**: Multi-device management not yet functional
- **No audit logging**: Administrative actions are not recorded

## Design Limitations

- The agent is a Python application, not a Windows kernel driver. It cannot intercept operations at the kernel level.
- File monitoring via watchdog is event-based but does not guarantee interception before a file copy completes.
- USB device control requires appropriate OS-level permissions.

## Security Limitations

- JWT secret must be manually rotated
- No rate limiting on API endpoints
- No input sanitization beyond Pydantic validation
- CORS is configured for development (localhost origins)
