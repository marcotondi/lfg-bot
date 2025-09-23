# src/handlers/admin.py

"""
Command handlers for admins.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler

from src.models import table as table_model
from src.models import user as user_model
from src.utils.decorators import admin_required

logger = logging.getLogger(__name__)

@admin_required
async def tables(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            f"<b>{table['game']}</b>\n" f"Max players: {table['max_players']}",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )


EDIT_DESCRIPTION, EDIT_MAX_PLAYERS = range(2)

@admin_required
async def edit_table_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    await query.edit_message_text(text=f"Please send the new {query.data.split('_')[1]}.")
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


def tables_handler() -> CommandHandler:
    """Returns the tables command handler for admins."""
    return CommandHandler("tables", tables)

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
                await context.bot.send_message(chat_id=user["telegram_id"], text=message, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to send message to {user['telegram_id']}: {e}")

    await update.message.reply_text("Tables published successfully!")

def publish_tables_handler() -> CommandHandler:
    """Returns the publish tables command handler."""
    return CommandHandler("publishTables", publish_tables)

@admin_required
async def set_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets a user as a master."""
    try:
        user_id = int(context.args[0])
        user_model.set_master(user_id, True)
        await update.message.reply_text(f"User {user_id} is now a master.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /setMaster <user_id>")

def set_master_handler() -> CommandHandler:
    """Returns the set master command handler."""
    return CommandHandler("setMaster", set_master)

@admin_required
async def unset_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsets a user as a master."""
    try:
        user_id = int(context.args[0])
        user_model.set_master(user_id, False)
        await update.message.reply_text(f"User {user_id} is no longer a master.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /unsetMaster <user_id>")

def unset_master_handler() -> CommandHandler:
    """Returns the unset master command handler."""
    return CommandHandler("unsetMaster", unset_master)

@admin_required
async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets a user as an admin."""
    try:
        user_id = int(context.args[0])
        user_model.set_admin(user_id, True)
        await update.message.reply_text(f"User {user_id} is now an admin.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /setAdmin <user_id>")

def set_admin_handler() -> CommandHandler:
    """Returns the set admin command handler."""
    return CommandHandler("setAdmin", set_admin)

@admin_required
async def unset_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsets a user as an admin."""
    try:
        user_id = int(context.args[0])
        user_model.set_admin(user_id, False)
        await update.message.reply_text(f"User {user_id} is no longer an admin.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /unsetAdmin <user_id>")

def unset_admin_handler() -> CommandHandler:
    """Returns the unset admin command handler."""
    return CommandHandler("unsetAdmin", unset_admin)
