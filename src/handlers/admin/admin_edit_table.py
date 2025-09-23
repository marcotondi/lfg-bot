# src/handlers/admin.py

"""
Command handlers for admins.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from src.models import table as table_model
from src.utils.decorators import admin_required
from src.utils.telegram_helpers import cancel

logger = logging.getLogger(__name__)


EDIT_DESCRIPTION, EDIT_MAX_PLAYERS = range(2)


@admin_required
async def edit_table_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handles the edit table callback."""
    query = update.callback_query
    table_id = int(query.data.split("_")[1])
    context.user_data["table_id"] = table_id
    keyboard = [
        [InlineKeyboardButton("Description", callback_data="edit_description")],
        [InlineKeyboardButton("Max Players", callback_data="edit_max_players")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="What do you want to edit?", reply_markup=reply_markup
    )
    return 0


@admin_required
async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the new value for the chosen field."""
    query = update.callback_query
    context.user_data["edit_choice"] = query.data
    await query.edit_message_text(
        text=f"Please send the new {query.data.split('_')[1]}."
    )
    return 1


@admin_required
async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Updates the table with the new value."""
    table_id = context.user_data["table_id"]
    edit_choice = context.user_data["edit_choice"]
    new_value = update.message.text
    table = table_model.get_table_by_id(table_id)

    if edit_choice == "edit_description":
        table_model.update_table(table_id, new_value, table["max_players"])
    elif edit_choice == "edit_max_players":
        table_model.update_table(table_id, table["description"], int(new_value))

    await update.message.reply_text("Table updated successfully!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Edit cancelled.")
    return ConversationHandler.END
