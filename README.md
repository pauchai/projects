# Project Collaboration Platform

A platform where users create projects and attract participants. Built with
Domain-Driven Design (DDD), Hexagonal Architecture, and Test-Driven Development
(TDD).

## Tech Stack

| Layer    | Technology                                                        |
|----------|-------------------------------------------------------------------|
| Backend  | Python 3.12, FastAPI, SQLAlchemy (Core), PostgreSQL 16, PyJWT     |
| Frontend | React 19, TypeScript 5.9, Vite 8, Tailwind CSS 4, shadcn/ui      |
| State    | Zustand (auth), TanStack Query (server state)                     |
| Infra    | Docker Compose, nginx                                             |

## Architecture

The system is split into two **Bounded Contexts** — each with its own domain
model, application layer, and infrastructure. The frontend is a standalone SPA
that communicates with the backend via REST.

```mermaid
graph TB
    subgraph Frontend ["Frontend (React SPA)"]
        Pages["Pages<br/>Login / Register / Projects / Profile"]
        Hooks["Hooks<br/>TanStack Query + Zustand"]
        ApiClient["API Client<br/>fetch + JWT injection"]
    end

    subgraph Backend ["Backend (FastAPI)"]
        subgraph Auth ["Auth Context"]
            AuthAPI["API Layer<br/>/auth/register, /auth/login, /auth/me"]
            AuthApp["Application Layer<br/>RegisterUser, Authenticate"]
            AuthDomain["Domain Layer<br/>User, Credential, Protocols"]
            AuthInfra["Infrastructure Layer<br/>Bcrypt, JWT, SQLAlchemy"]
        end

        subgraph ProjectCollab ["Project Collaboration Context"]
            ProjAPI["API Layer<br/>/projects/*, 14 endpoints"]
            ProjApp["Application Layer<br/>13 Use Cases"]
            ProjDomain["Domain Layer<br/>Project, Membership,<br/>ApplicationForm, SkillTag"]
            ProjInfra["Infrastructure Layer<br/>SQLAlchemy Core Repository"]
        end
    end

    subgraph DB ["PostgreSQL 16"]
        AuthTables["auth_users<br/>auth_credentials"]
        ProjTables["projects<br/>memberships<br/>applications<br/>skill_tags"]
    end

    Pages --> Hooks --> ApiClient
    ApiClient -- "HTTP + Bearer JWT" --> AuthAPI
    ApiClient -- "HTTP + Bearer JWT" --> ProjAPI

    AuthAPI --> AuthApp --> AuthDomain
    AuthApp --> AuthInfra
    AuthInfra --> AuthTables

    ProjAPI --> ProjApp --> ProjDomain
    ProjApp --> ProjInfra
    ProjInfra --> ProjTables

    AuthDomain -. "Protocols (Ports)" .-> AuthInfra
    ProjDomain -. "Protocols (Ports)" .-> ProjInfra
```

**Dependency rule:** Domain layers have zero external imports. Infrastructure
implements domain-defined Protocols (Ports). Application layer orchestrates
domain objects and calls Ports.

## Project Structure

```
.
├── src/
│   ├── auth/                          # Auth Bounded Context
│   │   ├── domain/                    #   User, Credential, Protocols
│   │   ├── application/               #   RegisterUser, Authenticate
│   │   ├── infrastructure/            #   Bcrypt, JWT, SQLAlchemy
│   │   └── api/                       #   FastAPI routes + dependencies
│   └── project_collaboration/         # Project Collaboration Context
│       ├── domain/                    #   Project aggregate, events, Protocols
│       ├── application/               #   13 use cases
│       ├── infrastructure/            #   SQLAlchemy Core repo, UoW
│       └── api/                       #   FastAPI routes + dependencies
├── tests/
│   ├── auth/                          # Auth tests (unit + integration)
│   └── project_collaboration/         # Project Collab tests (unit + integration)
│       ├── domain/
│       ├── application/
│       ├── integration/
│       ├── fakes/                     #   In-memory repo & UoW for unit tests
│       └── factories.py               #   Test data builders
├── frontend/
│   ├── src/
│   │   ├── api/                       # API client, types, fetch wrapper
│   │   ├── hooks/                     # TanStack Query hooks
│   │   ├── stores/                    # Zustand auth store
│   │   ├── pages/                     # 7 pages (register, login, projects, etc.)
│   │   └── components/                # UI components (shadcn/ui + custom)
│   ├── Dockerfile                     # Multi-stage: node build -> nginx
│   └── nginx.conf                     # SPA fallback + API reverse proxy
├── docker-compose.yml                 # PostgreSQL (dev + test) + frontend
├── pyproject.toml                     # Poetry config
└── AGENTS.md                          # Coding conventions for AI agents
```

## Prerequisites

- **Python 3.12+** and [Poetry](https://python-poetry.org/docs/#installation)
- **Node.js 22+** and npm
- **Docker** and **Docker Compose**

## Quick Start

### 1. Start the databases

```bash
docker compose up -d postgres postgres-test
```

This starts two PostgreSQL instances:

| Service         | Port | Database                       | User          |
|-----------------|------|--------------------------------|---------------|
| `postgres`      | 5434 | `project_collaboration`        | `collab`      |
| `postgres-test` | 5433 | `project_collaboration_test`   | `collab_test` |

### 2. Install backend dependencies

```bash
poetry install
```

### 3. Create database tables

No migrations (Alembic) yet — tables are created programmatically:

```bash
poetry run python -c "
from project_collaboration.infrastructure.database import get_engine, create_tables
from auth.infrastructure.database import create_tables as create_auth_tables
engine = get_engine()
create_tables(engine)
create_auth_tables(engine)
print('Tables created.')
"
```

### 4. Run the backend

```bash
poetry run uvicorn project_collaboration.api.app:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Interactive docs (Swagger UI)
at `http://localhost:8000/docs`.

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

### 6. Run the frontend dev server

```bash
npm run dev
```

Open `http://localhost:5173` in your browser. The Vite dev server proxies `/api`
requests to the backend at `localhost:8000`.

## Environment Variables

All variables have sensible defaults for local development. Override them as
needed for other environments.

| Variable             | Default                                                                  | Description                          |
|----------------------|--------------------------------------------------------------------------|--------------------------------------|
| `DATABASE_URL`       | `postgresql://collab:collab@localhost:5434/project_collaboration`         | PostgreSQL connection string         |
| `JWT_SECRET`         | `dev-secret-change-me`                                                   | Secret key for signing JWT tokens    |
| `JWT_ALGORITHM`      | `HS256`                                                                  | JWT signing algorithm                |
| `JWT_EXPIRE_MINUTES` | `60`                                                                     | Token expiration time in minutes     |
| `CORS_ORIGINS`       | `http://localhost:5173,http://localhost:3000`                             | Comma-separated allowed CORS origins |

> **Production warning:** Always set `JWT_SECRET` to a strong, unique value.
> Never use the default in production.

## Running Tests

### Backend (375 tests)

```bash
# Full suite
poetry run pytest

# Specific test file
poetry run pytest tests/project_collaboration/application/test_search_projects.py

# By test name
poetry run pytest -k test_confirm_sets_confirmed_flag

# Verbose with output
poetry run pytest -xvs
```

Requires the test database to be running (`docker compose up -d postgres-test`).

### Frontend (type-check + build)

```bash
cd frontend
npm run build
```

## Docker

### Development setup (recommended)

Run databases in Docker, backend and frontend on the host:

```bash
# Start databases
docker compose up -d postgres postgres-test

# Backend (in project root)
poetry run uvicorn project_collaboration.api.app:app --reload --port 8000

# Frontend (in frontend/)
cd frontend && npm run dev
```

### Frontend container

The frontend can also be built and served via Docker:

```bash
docker compose up -d frontend
```

This builds the React app and serves it via nginx on `http://localhost:3000`.

> **Known limitation:** The nginx config inside the frontend container proxies
> API requests to `http://backend:8000`, but there is no `backend` service in
> `docker-compose.yml`. The frontend container currently works for serving
> static assets only. For full-stack Docker deployment, a backend service needs
> to be added to `docker-compose.yml`.

## Interactive API Docs

With the backend running, visit:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

All project endpoints require a JWT token (`Authorization: Bearer <token>`).
Get one by registering via `POST /auth/register` and logging in via
`POST /auth/login`.
