# src/handlers/admin/tables.py

"""
Command handlers for admins.
"""

import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.models import table as table_model
from src.models import user as user_model
from src.utils.decorators import admin_required

logger = logging.getLogger(__name__)


@admin_required
async def publish_tables(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the list of active tables to all interested players."""
    active_tables = table_model.get_active_tables()
    if not active_tables:
        await update.message.reply_text("No active tables to publish.")
        return

    users = user_model.get_all_users()
    message = "<b>Active tables for the next game day:</b>\n\n"
    for table in active_tables:
        message += f"- {table['game']}\n"

    for user in users:
        if not user["mute"]:
            try:
                await context.bot.send_message(
                    chat_id=user["telegram_id"], text=message, parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send message to {user['telegram_id']}: {e}")

    await update.message.reply_text("Tables published successfully!")


def publish_tables_handler() -> CommandHandler:
    """Returns the publish tables command handler."""
    return CommandHandler("publishTables", publish_tables)
