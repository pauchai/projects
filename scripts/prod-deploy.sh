#!/usr/bin/env bash
# =============================================================================
# Deploy the production environment.
#
# Merges .env.common + .env.prod → .env.temp, ensures acme.json exists,
# builds images and starts containers in detached mode.
#
# Usage:
#   ./scripts/prod-deploy.sh
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Merging .env.common + .env.prod → .env.temp"
cat .env.common .env.prod > .env.temp

# Ensure acme.json exists with correct permissions (Let's Encrypt storage)
if [ ! -f traefik/acme.json ]; then
  echo "==> Creating traefik/acme.json with restricted permissions"
  touch traefik/acme.json
  chmod 600 traefik/acme.json
fi

# Ensure dashboard-auth.txt exists
if [ ! -f traefik/dashboard-auth.txt ]; then
  echo "WARNING: traefik/dashboard-auth.txt not found."
  echo "  Generate it with: htpasswd -nB admin > traefik/dashboard-auth.txt"
  echo "  The Traefik dashboard will not be accessible without it."
fi

echo "==> Building and deploying production environment..."
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.temp \
  up --build -d "$@"

echo "==> Production environment is running."
echo "    View logs: ./scripts/prod-logs.sh"
