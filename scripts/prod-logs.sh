#!/usr/bin/env bash
# =============================================================================
# Tail logs from the production environment.
#
# Usage:
#   ./scripts/prod-logs.sh              # all services
#   ./scripts/prod-logs.sh backend      # specific service
#   ./scripts/prod-logs.sh -n 100       # last 100 lines
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.temp \
  logs -f "$@"
