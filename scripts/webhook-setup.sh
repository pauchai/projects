#!/usr/bin/env bash
# =============================================================================
# Set the Telegram webhook for production.
#
# This tells Telegram to send updates to the backend /api/telegram/webhook
# endpoint instead of using polling.
#
# Usage:
#   ./scripts/webhook-setup.sh <domain> <bot_token>
#
# Example:
#   ./scripts/webhook-setup.sh yourdomain.com 123456:ABC-DEF
# =============================================================================
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <domain> <bot_token>"
  echo "Example: $0 yourdomain.com 123456:ABC-DEF"
  exit 1
fi

DOMAIN="$1"
BOT_TOKEN="$2"
WEBHOOK_URL="https://${DOMAIN}/api/telegram/webhook"

echo "==> Setting Telegram webhook to: ${WEBHOOK_URL}"

RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}")

echo "==> Telegram API response:"
echo "${RESPONSE}" | python3 -m json.tool 2>/dev/null || echo "${RESPONSE}"

# Verify
echo ""
echo "==> Verifying webhook info..."
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" \
  | python3 -m json.tool 2>/dev/null
