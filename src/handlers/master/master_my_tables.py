# src/handlers/master.py

"""
Command handlers for masters.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes
)

from src.models import user as user_model
from src.models import table as table_model
from src.utils.decorators import master_required

logger = logging.getLogger(__name__)

@master_required
async def my_tables(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a list of the master's tables with edit buttons."""
    user = user_model.get_telegram_user(update.effective_user.id)
    tables = table_model.get_tables_by_master_id(user["id"])

    if not tables:
        await update.message.reply_text("You have no tables.")
        return

    await update.message.reply_text("Here are your tables:")
    for table in tables:
        status = "Active" if table["active"] else "Inactive"
        keyboard = [
            [InlineKeyboardButton("Edit", callback_data=f"master_edit_{table['id']}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"<b>{table['game']}</b> ({status})\n"
            f"<b>{table['name']}</b> ({status})\n\n"
            f"<i>{table['description']}</i>\n\n"
            f"Max players: {table['max_players']}",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

def my_tables_handler() -> CommandHandler:
    """Returns the /mytables command handler."""
    return CommandHandler("mytables", my_tables)