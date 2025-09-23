# src/handlers/common/mute.py

"""
Common command handlers for all users.
"""

import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.models import user as user_model

logger = logging.getLogger(__name__)


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Opts the user out of future notifications."""
    message = update.message
    if not message:
        return

    user = user_model.get_user(update.effective_user.id)
    if user["mute"]:
        user_model.mute_user(update.effective_user.id, False)
        await message.reply_text("🔊 You will now receive notifications.")
    else:
        user_model.mute_user(update.effective_user.id, True)
        await message.reply_text("🔇 You will no longer receive notifications.")


def mute_handler() -> CommandHandler:
    """Returns the mute command handler."""
    return CommandHandler("mute", mute)
