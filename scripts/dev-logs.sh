#!/usr/bin/env bash
# =============================================================================
# Tail logs from the development environment.
#
# Usage:
#   ./scripts/dev-logs.sh              # all services
#   ./scripts/dev-logs.sh backend      # specific service
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  --env-file .env.temp \
  logs -f "$@"
