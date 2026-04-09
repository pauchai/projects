# Project Collaboration Platform

A platform where users create projects and attract participants. Built with
Domain-Driven Design (DDD), Hexagonal Architecture, and Test-Driven Development
(TDD).

## Tech Stack

| Layer    | Technology                                                        |
|----------|-------------------------------------------------------------------|
| Backend  | Python 3.12, FastAPI, SQLAlchemy (ORM), PostgreSQL 16, PyJWT, httpx |
| Auth     | JWT (email/password), Google OAuth 2.0 (popup flow)               |
| Frontend | React 19, TypeScript 5.9, Vite 8, Tailwind CSS 4, shadcn/ui      |
| State    | Zustand (auth), TanStack Query (server state)                     |
| Infra    | Docker Compose, Traefik (reverse proxy + SSL), nginx (static)     |

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
            AuthAPI["API Layer<br/>/auth/register, /auth/login, /auth/me<br/>/auth/oauth/google/*"]
            AuthApp["Application Layer<br/>RegisterUser, Authenticate,<br/>AuthenticateWithOAuth"]
            AuthDomain["Domain Layer<br/>User, Credential, Protocols"]
            AuthInfra["Infrastructure Layer<br/>Bcrypt, JWT, SQLAlchemy ORM,<br/>GoogleOAuthClient"]
        end

        subgraph ProjectCollab ["Project Collaboration Context"]
            ProjAPI["API Layer<br/>/projects/*, 14 endpoints"]
            ProjApp["Application Layer<br/>13 Use Cases"]
            ProjDomain["Domain Layer<br/>Project, Membership,<br/>ApplicationForm, SkillTag"]
            ProjInfra["Infrastructure Layer<br/>SQLAlchemy ORM Repository"]
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
│   │   ├── application/               #   RegisterUser, Authenticate, OAuth
│   │   ├── infrastructure/            #   Bcrypt, JWT, SQLAlchemy ORM, Google OAuth
│   │   └── api/                       #   FastAPI routes + dependencies
│   └── project_collaboration/         # Project Collaboration Context
│       ├── domain/                    #   Project aggregate, events, Protocols
│       ├── application/               #   13 use cases
│       ├── infrastructure/            #   SQLAlchemy ORM repo, UoW
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
│   └── nginx.conf                     # SPA fallback (API routing via Traefik)
├── docker-compose.yml                 # Base service definitions (no ports)
├── docker-compose.dev.yml             # Dev overlay: Traefik HTTP + hot reload
├── docker-compose.prod.yml            # Prod overlay: Traefik HTTPS + Let's Encrypt
├── traefik/
│   ├── traefik-dev.yml                # Traefik config: HTTP, debug logging
│   └── traefik-prod.yml               # Traefik config: HTTPS + ACME
├── scripts/
│   ├── dev-start.sh                   # Start development environment
│   ├── dev-stop.sh                    # Stop development environment
│   ├── dev-logs.sh                    # Tail dev logs
│   ├── prod-deploy.sh                 # Build & deploy production
│   ├── prod-logs.sh                   # Tail prod logs
│   ├── webhook-setup.sh              # Set Telegram webhook for prod
│   ├── telegram_bot_dev.py            # Telegram bot polling runner
│   └── telegram_bot_handler.py        # Shared bot handler logic
├── .env.example                       # Environment variable template
├── .env.common                        # Shared env vars (DB name, JWT algo)
├── .env.dev                           # Dev-specific env vars
├── .env.prod                          # Prod-specific env vars
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

### 2. Configure environment

```bash
cp .env.example .env
```

All variables have sensible defaults for local development — no edits required to
get started. See [Environment Variables](#environment-variables) for details and
[OAuth Setup](#oauth-setup-optional) if you want Google Sign-In.

### 3. Install backend dependencies

```bash
poetry install
```

### 4. Create database tables

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

### 5. Run the backend

```bash
poetry run uvicorn project_collaboration.api.app:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Interactive docs (Swagger UI)
at `http://localhost:8000/docs`.

### 6. Install frontend dependencies

```bash
cd frontend
npm install
```

### 7. Run the frontend dev server

```bash
npm run dev
```

Open `http://localhost:5173` in your browser. The Vite dev server proxies `/api`
requests to the backend at `localhost:8000`.

## Environment Variables

Copy the template and adjust as needed:

```bash
cp .env.example .env
```

All variables have sensible defaults for local development. See `.env.example`
for the full list with comments.

### Core Variables

| Variable             | Default                                                                  | Description                          |
|----------------------|--------------------------------------------------------------------------|--------------------------------------|
| `DATABASE_URL`       | `postgresql://collab:collab@localhost:5434/project_collaboration`         | PostgreSQL connection string         |
| `JWT_SECRET`         | `dev-secret-change-me-in-production`                                     | Secret key for signing JWT tokens    |
| `JWT_ALGORITHM`      | `HS256`                                                                  | JWT signing algorithm                |
| `JWT_EXPIRE_MINUTES` | `60`                                                                     | Token expiration time in minutes     |
| `CORS_ORIGINS`       | `http://localhost:5173,http://localhost:3000,http://localhost:3001`       | Comma-separated allowed CORS origins |

> **Production warning:** Always set `JWT_SECRET` to a strong, unique value of
> at least 32 characters. Never use the default in production.

### OAuth Providers (Optional)

OAuth credentials follow the naming convention `OAUTH_<PROVIDER>_<CREDENTIAL>`.
Leave empty to disable a provider — the UI will hide its sign-in button.

| Variable                       | Default | Description                      |
|--------------------------------|---------|----------------------------------|
| `OAUTH_GOOGLE_CLIENT_ID`      | *(empty)* | Google OAuth 2.0 client ID    |
| `OAUTH_GOOGLE_CLIENT_SECRET`  | *(empty)* | Google OAuth 2.0 client secret|
| `OAUTH_GOOGLE_REDIRECT_URI`   | *(empty)* | OAuth callback URL            |

Additional providers (GitHub, Microsoft, Discord) will follow the same pattern.
See [OAuth Setup](#oauth-setup-optional) for configuration instructions.

## OAuth Setup (Optional)

The platform supports social login via OAuth 2.0. Each provider is optional —
if credentials are not configured, the corresponding sign-in button is hidden.

### Google Sign-In

1. Go to [Google Cloud Console — Credentials](https://console.cloud.google.com/apis/credentials).
2. Create an **OAuth 2.0 Client ID** (application type: "Web application").
3. Add authorized redirect URIs:
   - Development: `http://localhost:5173/oauth/callback`
   - Production: `https://yourdomain.com/oauth/callback`
4. Copy the client ID and client secret into your `.env`:
   ```
   OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
   OAUTH_GOOGLE_REDIRECT_URI=http://localhost:5173/oauth/callback
   ```
5. Restart the backend. The "Sign in with Google" button will appear on the
   login and registration pages.

**How it works:** The frontend opens a popup window for Google authorization.
After the user consents, Google redirects back with an authorization code. The
backend exchanges this code for user info and either creates a new account or
links the Google credential to an existing account with the same email.

## Running Tests

### Backend (433 tests)

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

## Docker (Full Stack)

The project uses a **base + overlay** Docker Compose architecture with
[Traefik](https://traefik.io/) as the reverse proxy in both dev and prod.

```
docker-compose.yml          # Base: service definitions (no ports, no volumes)
docker-compose.dev.yml      # Dev overlay: Traefik HTTP, hot reload, *.localhost
docker-compose.prod.yml     # Prod overlay: Traefik HTTPS + Let's Encrypt
```

Environment variables are split into three files:

| File           | Purpose                                         |
|----------------|-------------------------------------------------|
| `.env.common`  | Shared between dev and prod (DB name, JWT algo) |
| `.env.dev`     | Dev-specific (weak passwords, HTTP URLs)        |
| `.env.prod`    | Prod-specific (strong passwords, domain, HTTPS) |

The helper scripts merge `.env.common` + `.env.{dev|prod}` into a temporary
`.env.temp` automatically.

---

### Development Environment

```bash
# 1. Fill in .env.common and .env.dev with your values
#    (sensible defaults are provided — only Telegram bot token is required
#     if you want the bot to work)

# 2. Start everything
./scripts/dev-start.sh
```

This builds and starts all services with Traefik routing:

| URL                              | Service                    |
|----------------------------------|----------------------------|
| `http://app.localhost`           | Frontend (Vite dev server) |
| `http://app.localhost/api`       | Backend (FastAPI)          |
| `http://app.localhost/api/docs`  | Swagger UI                 |
| `http://traefik.localhost:8080`  | Traefik dashboard          |

All `*.localhost` domains resolve automatically — no `/etc/hosts` edits needed.

**Hot reload** is enabled for all services:
- **Backend:** `uvicorn --reload` + volume mount of `./src`
- **Frontend:** Vite dev server + volume mount of `./frontend/src`
- **Telegram bot:** volume mounts of `./src` and `./scripts`

```bash
# Stop the environment
./scripts/dev-stop.sh

# Tail logs (all services or specific)
./scripts/dev-logs.sh
./scripts/dev-logs.sh backend
```

#### Manual setup (without Docker)

For development without Docker, start databases manually and run services
directly:

```bash
# Start databases only
docker compose up -d postgres
docker compose --profile test up -d postgres-test

# Backend (in project root)
cp .env.example .env
poetry install
poetry run uvicorn project_collaboration.api.app:app --reload --port 8000

# Frontend (in frontend/)
cd frontend && npm install && npm run dev
```

The Vite dev server proxies `/api` requests to `localhost:8000`. Open
`http://localhost:5173` in your browser.

---

### Production Deployment

The production setup uses Traefik with automatic HTTPS via Let's Encrypt on a
DigitalOcean Droplet (or any server with Docker).

#### Prerequisites

1. A server with Docker and Docker Compose installed.
2. A domain with DNS A record pointing to the server's IP.
3. (Optional) A CNAME record for `www` pointing to the bare domain.

#### Deploy

```bash
# 1. Fill in .env.common with real OAuth credentials
# 2. Fill in .env.prod:
#    - DOMAIN=yourdomain.com
#    - ACME_EMAIL=admin@yourdomain.com
#    - POSTGRES_PASSWORD=<strong-password>
#    - JWT_SECRET=<generate: python -c "import secrets; print(secrets.token_urlsafe(48))">
#    - OAUTH_TELEGRAM_BOT_TOKEN=<prod-bot-token>

# 3. Generate Traefik dashboard credentials
sudo apt-get install -y apache2-utils   # if htpasswd not available
htpasswd -nB admin > traefik/dashboard-auth.txt

# 4. Deploy
./scripts/prod-deploy.sh

# 5. (Optional) Set Telegram webhook for prod bot
./scripts/webhook-setup.sh yourdomain.com <bot-token>
```

Production URLs:

| URL                                  | Service                          |
|--------------------------------------|----------------------------------|
| `https://yourdomain.com`             | Frontend (nginx + built React)   |
| `https://yourdomain.com/api`         | Backend (FastAPI, 2 workers)     |
| `https://traefik.yourdomain.com`     | Traefik dashboard (Basic Auth)   |

All services have `restart: unless-stopped`. HTTP is automatically redirected
to HTTPS. SSL certificates are provisioned and renewed by Traefik via
Let's Encrypt.

```bash
# View production logs
./scripts/prod-logs.sh
./scripts/prod-logs.sh backend
```

---

### Running Tests

Requires the test database:

```bash
docker compose --profile test up -d postgres-test
```

### Environment

The base `docker-compose.yml` parametrizes all secrets via environment variables.
Docker-specific overrides (container hostnames) are set in compose files:

| Variable        | Docker Value                                                             | Reason                                  |
|-----------------|--------------------------------------------------------------------------|-----------------------------------------|
| `DATABASE_URL`  | `postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/...`   | Container hostname `postgres`, not `localhost` |
| `REDIS_URL`     | `redis://redis:6379/0`                                                   | Container hostname `redis`              |
| `PYTHONPATH`    | `/app/src`                                                               | Module resolution inside container      |

CORS origins and frontend URLs are set per-environment in the overlay files.

## Interactive API Docs

With the backend running, visit:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

All project endpoints require a JWT token (`Authorization: Bearer <token>`).
Get one by registering via `POST /auth/register` and logging in via
`POST /auth/login`.
