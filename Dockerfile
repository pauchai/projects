# ---------- Backend Dockerfile ----------
# Multi-stage: builder installs deps, runner runs the app

FROM python:3.12-slim AS builder

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without virtualenv, to /root/.cache)
# --no-root skips installing the local project package itself
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy source code (must be after install so it doesn't invalidate cache on every change)
COPY src/ src/

# ---------- Runner ----------
FROM python:3.12-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /root/.cache/pip /root/.cache/pip
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY src/ src/

# Expose backend port
EXPOSE 8000

# Run with uvicorn (--reload for dev auto-reload on code changes)
# Use host network mode for better compatibility with volume mounts
CMD ["uvicorn", "project_collaboration.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]