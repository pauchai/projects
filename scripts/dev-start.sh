#!/usr/bin/env bash
# =============================================================================
# Start the development environment.
#
# Merges .env.common + .env.dev → .env.temp, then starts docker compose
# with the dev overlay.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Merging .env.common + .env.dev → .env.temp"
cat .env.common .env.dev > .env.temp

echo "==> Starting development environment..."
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  --env-file .env.temp \
  up --build "$@"
