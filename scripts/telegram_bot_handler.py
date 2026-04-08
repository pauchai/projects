"""Telegram bot handler — processes /start commands for auth flow.

This module contains the bot handler logic that is used both by the
dev polling script and (in the future) by the production webhook handler.

The handler:
1. Receives /start <auth_code> from a user.
2. Calls the backend's internal /bot-callback endpoint with the auth_code
   and the user's Telegram data.
3. Sends the user a link to complete authentication on the website.
"""

from __future__ import annotations

import logging

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

logger = logging.getLogger(__name__)


def create_dispatcher(
    backend_url: str,
    frontend_url: str,
) -> Dispatcher:
    """Create an aiogram Dispatcher with the /start handler configured.

    Args:
        backend_url: Base URL of the backend API (e.g., http://localhost:8000).
        frontend_url: Base URL of the frontend (e.g., http://localhost:3001).
    """
    dp = Dispatcher()

    @dp.message(CommandStart(deep_link=True))
    async def handle_start_with_auth_code(message: types.Message) -> None:
        """Handle /start <auth_code> — authenticate the user."""
        if message.from_user is None:
            return

        # Extract the auth_code from /start payload
        text = message.text or ""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "👋 Welcome!\n\nTo sign in, please use the link on the website.",
                parse_mode=ParseMode.HTML,
            )
            return

        auth_code = parts[1].strip()
        if not auth_code:
            await message.answer(
                "👋 Welcome!\n\nTo sign in, please use the link on the website.",
                parse_mode=ParseMode.HTML,
            )
            return

        telegram_user = message.from_user

        # Call the backend's internal bot-callback endpoint
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{backend_url}/auth/oauth/telegram/bot-callback",
                    json={
                        "auth_code": auth_code,
                        "telegram_user_id": str(telegram_user.id),
                        "telegram_username": telegram_user.username,
                        "telegram_first_name": telegram_user.first_name
                        or "Telegram User",
                    },
                )
        except httpx.HTTPError:
            logger.exception("Failed to call bot-callback endpoint")
            await message.answer(
                "❌ Something went wrong.\n\nPlease try again from the website.",
                parse_mode=ParseMode.HTML,
            )
            return

        if response.status_code != 200:
            logger.error(
                "Bot-callback failed: %s %s", response.status_code, response.text
            )
            await message.answer(
                "⏰ Authentication request not found or expired.\n\n"
                "Please start again from the website.",
                parse_mode=ParseMode.HTML,
            )
            return

        data = response.json()
        authorization_code = data["authorization_code"]
        state = data["state"]

        # Send the user a link to complete auth on the website
        auth_link = (
            f"{frontend_url}/oauth/callback?code={authorization_code}&state={state}"
        )

        await message.answer(
            "✨ Almost done!\n\n"
            f"Tap here to finish signing in and access your account:\n\n{auth_link}"
        )

    @dp.message(CommandStart())
    async def handle_start_no_payload(message: types.Message) -> None:
        """Handle /start without payload — welcome message."""
        await message.answer(
            "👋 Welcome!\n\n"
            "To sign in, please use the <b>Sign in with Telegram</b> "
            "button on the website.",
            parse_mode=ParseMode.HTML,
        )

    return dp
