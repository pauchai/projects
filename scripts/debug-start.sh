#!/usr/bin/env bash
# =============================================================================
# Start the development environment with debugpy (port 5678).
#
# Attach VS Code debugger via .vscode/launch.json → "Docker: Backend Debug"
# after the container has started.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Merging .env.common + .env.dev → .env.temp"
cat .env.common .env.dev > .env.temp

echo "==> Starting development environment with debug (port 5678)..."
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  -f docker-compose.debug.yml \
  --env-file .env.temp \
  up --build "$@"
