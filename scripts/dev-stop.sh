#!/usr/bin/env bash
# =============================================================================
# Stop the development environment and clean up .env.temp.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Stopping development environment..."
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  --env-file .env.temp \
  down "$@"

rm -f .env.temp
echo "==> Cleaned up .env.temp"
