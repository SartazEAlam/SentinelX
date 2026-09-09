# SentinelX — Deployment Guide

> Detailed deployment instructions will be added when containerized deployment is fully implemented.

## Development Deployment

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (optional)

### Quick Start

```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev

# Agent
cd agent
python -m sentinel_agent
```

### Docker Deployment

```bash
# Start PostgreSQL and backend
docker compose up -d

# Verify services
docker compose ps
```

## Production Considerations (Future)

- Use PostgreSQL instead of SQLite
- Configure proper JWT_SECRET
- Restrict CORS origins
- Enable HTTPS
- Set ENVIRONMENT=production
- Configure proper logging
- Set up monitoring and alerting
