# src/handlers/common/start.py

"""
Common command handlers for all users.
"""

import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.models import user as user_model

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and registers the user."""
    user = update.effective_user
    message = update.message

    # Early returns per sicurezza
    if not user:
        return
    if not message:
        return

    if not user_model.get_user(user.id):
        user_model.create_user(user.id, user.username, user.first_name, user.last_name)

    await message.reply_html(
        f"Hi {user.mention_html()}! Welcome to the GDR Salento Bot.",
    )


def start_handler() -> CommandHandler:
    """Returns the start command handler."""
    return CommandHandler("start", start)
