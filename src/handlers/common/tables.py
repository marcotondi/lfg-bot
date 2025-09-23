# src/handlers/common.py

"""
Common command handlers for all users.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from typing import Dict, Any, Optional

from src.models import registration as registration_model
from src.models import user as user_model
from src.models import table as table_model
from src.utils.telegram_helpers import safe_edit_message

logger = logging.getLogger(__name__)


def format_table_message(
    table: Dict[str, Any], master_name: Optional[str] = None, current_players: int = 0
) -> str:
    """
    Formatta un messaggio per una table di gioco seguendo il template fornito.

    Args:
        table: Dizionario con i dati della table dal database
        master_name: Nome del master (opzionale)
        current_players: Numero di giocatori attuali

    Returns:
        Stringa HTML formattata per Telegram
    """

    # Emoji per tipo di sessione
    type_icons = {"one_shot": "⚡", "campaign": "📚"}

    # Header stylizzato
    message = f"<b>{table['game'].upper()}</b> \n\n"

    # Tipo con stile
    type_icon = type_icons.get(table["type"], "🎮")
    if table["type"] == "one_shot":
        message += f"{type_icon} <b>Oneshot</b>\n"
    else:
        sessions_text = (
            f" ({table['num_sessions']} sessioni)"
            if "num_sessions" in table.keys()
            else ""
        )
        message += f"{type_icon} <b>Campagna</b>{sessions_text}\n"

    message += f"<i>{table['name']}</i>\n\n\n"
    message += f"<i>{table['description']}</i>\n\n"

    # Progress bar per i posti
    filled_slots = "🟦" * current_players
    empty_slots = "⬜" * (table["max_players"] - current_players)
    progress_bar = filled_slots + empty_slots

    message += f"👥 <b>Giocatori:</b> {current_players}/{table['max_players']}\n"
    message += f"{progress_bar}\n\n"

    # Master
    if master_name:
        message += f"🎭 <b>Master:</b> {master_name}\n"

    return message


async def tables(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the active tables for the next game day with rich formatting."""
    message = update.message
    if not message:
        return

    active_tables = table_model.get_active_tables()
    if not active_tables:
        await message.reply_text("No active tables for the next game day.")
        return

    user_id = update.effective_user.id
    for table in active_tables:
        # Check if the user is already registered for this table
        is_registered = registration_model.get_registration(table["id"], user_id)

        # Get current players count
        current_players = registration_model.get_registrations_count(table["id"])

        # Get master info
        master = user_model.get_user(table["master_id"])
        master_name = None
        if master:
            master_name = f"{master['first_name']} {master['last_name']}"
            if master.get("username"):
                master_name += f" (@{master['username']})"

        # Create buttons
        if is_registered:
            join_button = InlineKeyboardButton(
                "❌ Unjoin", callback_data=f"unjoin_{table['id']}"
            )
        else:
            if current_players >= table["max_players"]:
                join_button = InlineKeyboardButton(
                    "🚫 Table Full", callback_data=f"table_full_{table['id']}"
                )
            else:
                join_button = InlineKeyboardButton(
                    "✅ Join", callback_data=f"join_{table['id']}"
                )

        keyboard = [
            [
                join_button,
                InlineKeyboardButton(
                    "👥 Show Players", callback_data=f"show_{table['id']}"
                ),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Format the message using our advanced formatter
        formatted_message = format_table_message(table, master_name, current_players)

        # Send with image if available, otherwise just text
        try:
            if table["image"] is not None:
                await message.reply_photo(
                    photo=table["image"],
                    caption=formatted_message,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )
            else:
                await message.reply_text(
                    formatted_message,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )
        except Exception as e:
            logger.error(f"Si è verificato un errore: {e}", exc_info=True)
    # exc_info=True aggiunge automaticamente il traceback completo
            # Fallback to simple format if advanced formatting fails
            simple_message = (
                f"<b>ECCEZIONE</b>\n"
                f"<b>{table['game']}</b>\n"
                f"<b>{table['description']}</b>\n"
                f"Max players: {table['max_players']}\n"
                f"Current players: {current_players}"
            )
            await message.reply_text(
                simple_message,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )


async def join_table_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles the join table callback."""
    query = update.callback_query
    if not query:
        return

    table_id = int(query.data.split("_")[1])
    user = user_model.get_user(update.effective_user.id)

    # Get registration status, if any
    registration = registration_model.get_any_registration(table_id, user["id"])
    table = table_model.get_table_by_id(table_id)

    # Case 1: User is already actively registered.
    if registration and registration["is_active"]:
        await query.answer(text="You are already registered for this table.")
        return

    # Case 2: Table is full.
    if registration_model.get_registrations_count(table_id) >= table["max_players"]:
        await query.answer(text="This table is full.")
        return

    # Action: Join the table
    registration_model.create_registration(table_id, user["id"])
    await query.answer(text="✅ You have successfully joined the table!")

    # Update the message to show the "Unjoin" button
    keyboard = [
        [
            InlineKeyboardButton("❌ Unjoin", callback_data=f"unjoin_{table_id}"),
            InlineKeyboardButton("👥 Show Players", callback_data=f"show_{table_id}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)


async def unjoin_table_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles the unjoin table callback."""
    query = update.callback_query
    if not query:
        return

    table_id = int(query.data.split("_")[1])
    user = user_model.get_user(update.effective_user.id)

    if not registration_model.get_registration(table_id, user["id"]):
        await query.answer(text="You are not registered for this table.")
        return

    registration_model.unjoin_registration(table_id, user["id"])
    await query.answer(text="⚠️ You have successfully left the table.")

    # Update the message to show the "Join" button
    keyboard = [
        [
            InlineKeyboardButton("✅ Join", callback_data=f"join_{table_id}"),
            InlineKeyboardButton("👥 Show Players", callback_data=f"show_{table_id}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)


async def show_players_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles the show players callback with enhanced formatting."""
    query = update.callback_query
    if not query:
        return

    table_id = int(query.data.split("_")[1])
    table = table_model.get_table_by_id(table_id)
    master = user_model.get_user(table["master_id"])
    registrations = registration_model.get_registrations_for_table(table_id)

    # Header with game info
    message = f"🎮 <b>{table['game']}</b>\n"
    message += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    # Master info
    if master:
        message += f"🎭 <b>Master:</b> {master['first_name']} {master['last_name']}"
        if master.get("username"):
            message += f" (@{master['username']})"
        message += "\n\n"
    else:
        message += "🎭 <b>Master:</b> Information not available\n\n"

    # Players info
    message += f"👥 <b>Players ({len(registrations)}/{table['max_players']}):</b>\n"

    if not registrations:
        message += "   <i>No players registered yet</i>\n"
    else:
        for i, player in enumerate(registrations, 1):
            username = (
                f"@{player['username']}"
                if "username" in player.keys()
                else "no username"
            )
            message += (
                f"   {i}. {player['first_name']} {player['last_name']} ({username})\n"
            )

    # Available slots
    remaining_slots = table["max_players"] - len(registrations)
    if remaining_slots > 0:
        message += f"\n🟢 <b>{remaining_slots} slot{'s' if remaining_slots != 1 else ''} available</b>"
    else:
        message += "\n🔴 <b>Table is full</b>"

    # await query.edit_message_text(text=message, parse_mode="HTML")
    await safe_edit_message(query, message)


def tables_handler() -> CommandHandler:
    """Returns the tables command handler."""
    return CommandHandler("tables", tables)
