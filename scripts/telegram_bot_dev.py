#!/usr/bin/env python3
"""Development Telegram bot — runs in polling mode.

Usage:
    python scripts/telegram_bot_dev.py

Requires:
    - OAUTH_TELEGRAM_BOT_TOKEN env var (or in .env file)
    - Backend running at BACKEND_URL (default: http://localhost:8000)
    - Frontend running at FRONTEND_URL (default: http://localhost:3001)

This script is for local development only. In production, the bot
should be configured to use webhooks integrated into the FastAPI backend.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Add src/ to path so we can import from the project
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

# Load .env file if present
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from aiogram import Bot  # noqa: E402

from telegram_bot_handler import create_dispatcher  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the Telegram bot in polling mode."""
    bot_token = os.environ.get("OAUTH_TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.error(
            "OAUTH_TELEGRAM_BOT_TOKEN is not set. "
            "Please set it in .env or as an environment variable."
        )
        sys.exit(1)

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3001")

    logger.info("Starting Telegram bot in polling mode...")
    logger.info("Backend URL: %s", backend_url)
    logger.info("Frontend URL: %s", frontend_url)

    bot = Bot(token=bot_token)
    dp = create_dispatcher(backend_url=backend_url, frontend_url=frontend_url)

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
