# src/handlers/master.py

"""
Command handlers for masters.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.models import user as user_model
from src.models import table as table_model
from src.utils.decorators import master_required
from src.utils.telegram_helpers import cancel

logger = logging.getLogger(__name__)


# Conversation states for editing
EDIT_CHOICE, EDIT_VALUE = range(7, 9)


@master_required
async def edit_table_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handles the master edit table callback, ensuring ownership."""
    query = update.callback_query
    table_id = int(query.data.split("_")[2])  # e.g., master_edit_123

    # Security Check: Ensure the user is the master of this table
    user = user_model.get_telegram_user(update.effective_user.id)
    table = table_model.get_table_by_id(table_id)
    if not table or table["master_id"] != user["id"]:
        await query.answer(
            "You are not authorized to edit this table.", show_alert=True
        )
        return ConversationHandler.END

    context.user_data["table_id"] = table_id
    keyboard = [
        [InlineKeyboardButton("Description", callback_data="edit_description")],
        [InlineKeyboardButton("Max Players", callback_data="edit_max_players")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="What do you want to edit?", reply_markup=reply_markup
    )
    return EDIT_CHOICE


@master_required
async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the new value for the chosen field."""
    query = update.callback_query
    context.user_data["edit_choice"] = query.data
    await query.edit_message_text(
        text=f"Please send the new {query.data.split('_')[1]}."
    )
    return EDIT_VALUE


@master_required
async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Updates the table with the new value."""
    table_id = context.user_data["table_id"]
    edit_choice = context.user_data["edit_choice"]
    new_value = update.message.text
    table = table_model.get_table_by_id(table_id)

    # Security check is implicitly handled by the entry point, but good practice
    user = user_model.get_telegram_user(update.effective_user.id)
    if not table or table["master_id"] != user["id"]:
        await update.message.reply_text("Error: You are not the master of this table.")
        return ConversationHandler.END

    if edit_choice == "edit_description":
        table_model.update_table(table_id, new_value, table["max_players"])
    elif edit_choice == "edit_max_players":
        try:
            table_model.update_table(table_id, table["description"], int(new_value))
        except ValueError:
            await update.message.reply_text("Invalid number. Please send a valid number for max players.")
            return EDIT_VALUE

    await update.message.reply_text("Table updated successfully!")
    context.user_data.clear()
    return ConversationHandler.END


def master_edit_handler() -> ConversationHandler:
    """Returns the master edit conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_table_callback, pattern="^master_edit_")
        ],
        states={
            EDIT_CHOICE: [
                CallbackQueryHandler(
                    edit_choice, pattern="^(edit_description|edit_max_players)"
                )
            ],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
