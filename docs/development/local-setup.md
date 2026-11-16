# Local Development Setup Guide

**PLAGIX v1.0**  
**Status:** Phase 0.2 Implementation  
**Last updated:** 16 November 2026

---

## Prerequisites

1. **Docker Desktop** (with Docker Compose v2 enabled) running on Windows 11.
2. **PowerShell** (built-in Windows shell).
3. **Python 3.11+** (optional, only required if running host-side tests or linting outside Docker).

---

## 1. Environment Configuration

1. Copy the example environment file to create your local `.env` file:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` and verify configuration values (default dev credentials are pre-configured for local testing).

---

## 2. Starting the Development Stack

Start PostgreSQL, Redis, and the FastAPI backend using Docker Compose:

```powershell
docker compose up --build -d
```

### Verify Running Services & Health
Check container status and health checks:
```powershell
docker compose ps
```

Verify API liveness and database readiness via HTTP:
- Liveness: `http://localhost:8000/health/live`
- Readiness (checks PostgreSQL & Redis): `http://localhost:8000/health/ready`
- Interactive API Docs: `http://localhost:8000/docs`

---

## 3. Running Alembic Database Migrations

Migrations run automatically or can be executed manually inside the API container:

```powershell
docker compose exec api alembic upgrade head
```

To check current migration revision:
```powershell
docker compose exec api alembic current
```

To roll back the last migration:
```powershell
docker compose exec api alembic downgrade -1
```

---

## 4. Running Tests

Run pytest inside the API container against the real PostgreSQL database:

```powershell
docker compose exec api pytest
```

---

## 5. Host-Side vs. Container-Side Connections

| Component | Container-to-Container (Docker Network) | Host-Side (Windows / psql) |
|-----------|----------------------------------------|---------------------------|
| **PostgreSQL** | `db:5432` | `localhost:5432` |
| **Redis** | `redis:6379` | `localhost:6379` |
| **FastAPI API** | `api:8000` | `localhost:8000` |

---

## 6. Resetting the Local Database (Warning: Destructive)

If you need to completely reset the local database and run migrations from scratch:

```powershell
# Stop containers and remove volumes (DELETES DATA)
docker compose down -v

# Restart containers
docker compose up -d

# Run migrations again
docker compose exec api alembic upgrade head
```

---

## 7. Windows / PowerShell Troubleshooting

- **Port already in use**: If port 5432 or 8000 is occupied by a local PostgreSQL or service, stop the local service or change the port mapping in `compose.yaml`.
- **Docker daemon not running**: Ensure Docker Desktop is open and the whale icon is running in your Windows tray.
- **Line endings (CRLF vs LF)**: Ensure Git handles line endings correctly (`git config --global core.autocrlf false`) if running shell scripts.
