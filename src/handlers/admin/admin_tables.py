# src/handlers/admin/tables.py

"""
Command handlers for admins.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

from src.models import table as table_model
from src.utils.decorators import admin_required

logger = logging.getLogger(__name__)


@admin_required
async def tables_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reviews all inserted tables with inline buttons to edit."""
    all_tables = table_model.get_all_tables()
    if not all_tables:
        if not update.message:
            return  # Esci se non c'è messaggio

        await update.message.reply_text("No tables found.")
        return

    for table in all_tables:
        keyboard = [
            [InlineKeyboardButton("Edit", callback_data=f"edit_{table['id']}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"<b>{table['game']}</b>\nMax players: {table['max_players']}",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )


def tables_handler() -> CommandHandler:
    """Returns the tables command handler for admins."""
    return CommandHandler("tables", tables_admin)
