# src/handlers/common.py
"""
Common command handlers for all users.
"""

import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from sqlite3 import Row

from src.models import registration as registration_model
from src.models import user as user_model
from src.models import table as table_model
from src.utils.telegram_helpers import safe_edit_message

logger = logging.getLogger(__name__)


class HandlerError(Exception):
    """Base exception for handler operations."""
    pass


def format_table_message(
    table: Row, master_name: Optional[str] = None, current_players: int = 0
) -> str:
    """
    Formatta un messaggio per una table di gioco seguendo il template fornito.

    Args:
        table: Row object con i dati della table dal database
        master_name: Nome del master (opzionale)
        current_players: Numero di giocatori attuali

    Returns:
        Stringa HTML formattata per Telegram

    Raises:
        ValueError: If required table fields are missing
    """
    try:
        # Validazione campi obbligatori
        required_fields = ["game", "type", "name", "description", "max_players"]
        missing_fields = [
            field for field in required_fields if field not in table.keys()
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Emoji per tipo di sessione
        type_icons = {"one_shot": "⚡", "campaign": "📚"}

        # Header stylizzato
        message = f"<b>{table['game'].upper()}</b> \n\n"

        # Tipo con stile
        type_icon = type_icons.get(table["type"], "🎮")
        if table["type"] == "one_shot":
            message += f"{type_icon} <b>Oneshot</b>\n"
        else:
            sessions_text = ""
            if "num_sessions" in table.keys() and table["num_sessions"]:
                sessions_text = f" ({table['num_sessions']} sessioni)"
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

    except KeyError as e:
        logger.error(f"Missing table field: {e}")
        raise ValueError(f"Invalid table data: missing field {e}") from e


def row_get(row: Row, key: str, default=None):
    """
    Safe get for sqlite3.Row objects (equivalent to dict.get()).

    Args:
        row: sqlite3.Row object
        key: Column name
        default: Default value if key not found

    Returns:
        Value or default
    """
    try:
        return row[key] if key in row.keys() else default
    except (KeyError, IndexError):
        return default


def format_master_name(master: Optional[Row]) -> Optional[str]:
    """
    Formatta il nome del master con username se disponibile.

    Args:
        master: Row object con i dati del master

    Returns:
        Nome formattato o None se master non esiste
    """
    if not master:
        return None

    # Costruisci il nome
    name_parts = []
    first_name = row_get(master, "first_name")
    last_name = row_get(master, "last_name")

    if first_name:
        name_parts.append(first_name)
    if last_name:
        name_parts.append(last_name)

    name = " ".join(name_parts) if name_parts else "Unknown Master"

    # Aggiungi username se disponibile
    username = row_get(master, "username")
    if username:
        name += f" (@{username})"

    return name


def create_table_keyboard(
    table_id: int, is_registered: bool, is_full: bool
) -> InlineKeyboardMarkup:
    """
    Crea la keyboard inline per una table.

    Args:
        table_id: ID della table
        is_registered: Se l'utente è registrato
        is_full: Se la table è piena

    Returns:
        InlineKeyboardMarkup configurata
    """
    if is_registered:
        join_button = InlineKeyboardButton(
            "❌ Unjoin", callback_data=f"unjoin_{table_id}"
        )
    elif is_full:
        join_button = InlineKeyboardButton(
            "🚫 Table Full", callback_data=f"table_full_{table_id}"
        )
    else:
        join_button = InlineKeyboardButton("✅ Join", callback_data=f"join_{table_id}")

    keyboard = [
        [
            join_button,
            InlineKeyboardButton("👥 Show Players", callback_data=f"show_{table_id}"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def send_table_info(
    message,
    table: Row,
    master_name: Optional[str],
    current_players: int,
    reply_markup: InlineKeyboardMarkup,
) -> bool:
    """
    Invia le informazioni di una table con immagine se disponibile.

    Args:
        message: Telegram message object
        table: Row object con i dati della table
        master_name: Nome del master
        current_players: Numero giocatori attuali
        reply_markup: Keyboard inline

    Returns:
        True se inviato con successo, False altrimenti
    """
    formatted_message = format_table_message(table, master_name, current_players)

    try:
        image_url = row_get(table, "image")
        if image_url:
            await message.reply_photo(
                photo=image_url,
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
        return True

    except Exception as e:
        logger.error(f"Failed to send table info: {e}", exc_info=True)

        # Fallback to simple format
        try:
            game = row_get(table, "game", "Unknown Game")
            description = row_get(table, "description", "No description")
            max_players = row_get(table, "max_players", "N/A")

            simple_message = (
                f"<b>⚠️ Formatting Error</b>\n\n"
                f"<b>{game}</b>\n"
                f"{description}\n\n"
                f"Max players: {max_players}\n"
                f"Current players: {current_players}"
            )
            await message.reply_text(
                simple_message,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return True
        except Exception as fallback_error:
            logger.error(
                f"Fallback message also failed: {fallback_error}", exc_info=True
            )
            return False


async def tables(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Shows the active tables for the next game day with rich formatting.

    Usage: /tables
    """
    message = update.message
    if not message:
        logger.warning("tables command called without message")
        return

    telegram_id = update.effective_user.id

    try:
        user = user_model.get_telegram_user(telegram_id)

        # Get active tables
        active_tables = table_model.get_active_tables()

        if not active_tables:
            await message.reply_text(
                "📭 <b>No active tables</b>\n\n"
                "There are no tables available for the next game day.\n"
                "Check back later or contact a master to create one!",
                parse_mode="HTML",
            )
            return

        logger.info(f"Showing {len(active_tables)} active tables to user {user['id']}")

        # Send info for each table
        successful_sends = 0
        for table in active_tables:
            try:
                # Check registration status
                is_registered = registration_model.is_user_registered(
                    table["id"], user["id"]
                )

                # Get current players count
                current_players = registration_model.get_registrations_count(
                    table["id"]
                )

                # Check if table is full
                is_full = current_players >= table["max_players"]

                # Get master info
                master = user_model.get_user(table["master_id"])
                master_name = format_master_name(master)

                # Create keyboard
                reply_markup = create_table_keyboard(
                    table["id"], is_registered, is_full
                )

                # Send table info
                if await send_table_info(
                    message, table, master_name, current_players, reply_markup
                ):
                    successful_sends += 1

            except Exception as e:
                logger.error(
                    f"Failed to send table {table['id']}: {e}",
                    exc_info=True,
                )
                continue

        if successful_sends == 0:
            await message.reply_text(
                "⚠️ An error occurred while loading tables. Please try again later."
            )

    except Exception as e:
        logger.error(f"Fatal error in tables command: {e}", exc_info=True)
        await message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )


async def join_table_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handles the join table callback.

    Callback data format: join_{table_id}
    """
    query = update.callback_query
    if not query:
        logger.warning("join_table_callback called without query")
        return

    try:
        # Parse callback data
        try:
            table_id = int(query.data.split("_")[1])
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid callback data: {query.data}")
            await query.answer(text="❌ Invalid request", show_alert=True)
            return

        telegram_id = update.effective_user.id
        user = user_model.get_telegram_user(telegram_id)

        if not user:
            logger.error(f"User not found: {telegram_id}")
            await query.answer(
                text="❌ User not found. Please use /start first.", show_alert=True
            )
            return

        # Get table info
        table = table_model.get_table_by_id(table_id)
        if not table:
            logger.warning(f"Table not found: {table_id}")
            await query.answer(text="❌ Table not found", show_alert=True)
            return

        # Check if table is active
        is_active = row_get(table, "active", False)
        if not is_active:
            await query.answer(text="⚠️ This table is no longer active", show_alert=True)
            return

        # Check if already registered
        if registration_model.is_user_registered(table_id, user["id"]):
            await query.answer(text="ℹ️ You are already registered for this table.")
            return

        # Check if table is full
        capacity_info = registration_model.get_table_capacity_info(table_id)
        if capacity_info["is_full"]:
            await query.answer(text="🚫 This table is full.", show_alert=True)
            return

        # Join the table
        try:
            registration_model.create_registration(table_id, user["id"])
            logger.info(f"User {user_id} joined table {table_id}")
            await query.answer(text="✅ You have successfully joined the table!")

            # Update the keyboard
            keyboard = [
                [
                    InlineKeyboardButton(
                        "❌ Unjoin", callback_data=f"unjoin_{table_id}"
                    ),
                    InlineKeyboardButton(
                        "👥 Show Players", callback_data=f"show_{table_id}"
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)

        except registration_model.TableFullError:
            await query.answer(
                text="🚫 Table became full while you were joining!", show_alert=True
            )
        except registration_model.RegistrationAlreadyExistsError:
            await query.answer(text="ℹ️ You are already registered for this table.")

    except Exception as e:
        logger.error(f"Error in join_table_callback: {e}", exc_info=True)
        await query.answer(
            text="❌ An error occurred. Please try again.", show_alert=True
        )


async def unjoin_table_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handles the unjoin table callback.

    Callback data format: unjoin_{table_id}
    """
    query = update.callback_query
    if not query:
        logger.warning("unjoin_table_callback called without query")
        return

    try:
        # Parse callback data
        try:
            table_id = int(query.data.split("_")[1])
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid callback data: {query.data}")
            await query.answer(text="❌ Invalid request", show_alert=True)
            return

        telegram_id = update.effective_user.id
        user = user_model.get_telegram_user(telegram_id)

        if not user:
            logger.error(f"User not found: {telegram_id}")
            await query.answer(text="❌ User not found", show_alert=True)
            return

        # Check if registered
        if not registration_model.is_user_registered(table_id, user["id"]):
            await query.answer(text="ℹ️ You are not registered for this table.")
            return

        # Unjoin the table
        if registration_model.unjoin_registration(table_id, user["id"]):
            logger.info(f"User {user['id']} left table {table_id}")
            await query.answer(text="⚠️ You have successfully left the table.")

            # Update the keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Join", callback_data=f"join_{table_id}"),
                    InlineKeyboardButton(
                        "👥 Show Players", callback_data=f"show_{table_id}"
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)
        else:
            await query.answer(text="❌ Failed to leave the table. Please try again.")

    except Exception as e:
        logger.error(f"Error in unjoin_table_callback: {e}", exc_info=True)
        await query.answer(
            text="❌ An error occurred. Please try again.", show_alert=True
        )


async def show_players_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handles the show players callback with enhanced formatting.

    Callback data format: show_{table_id}
    """
    query = update.callback_query
    if not query:
        logger.warning("show_players_callback called without query")
        return

    try:
        # Parse callback data
        try:
            table_id = int(query.data.split("_")[1])
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid callback data: {query.data}")
            await query.answer(text="❌ Invalid request", show_alert=True)
            return

        # Get table info
        table = table_model.get_table_by_id(table_id)
        if not table:
            await query.answer(text="❌ Table not found", show_alert=True)
            return

        # Get master info
        master = user_model.get_user(table["master_id"])

        # Get registrations
        registrations = registration_model.get_registrations_for_table(table_id)

        # Build message
        message = f"🎮 <b>{table['game']}</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Master info
        if master:
            master_name = format_master_name(master)
            message += f"🎭 <b>Master:</b> {master_name}\n\n"
        else:
            message += "🎭 <b>Master:</b> <i>Information not available</i>\n\n"

        # Players info
        message += f"👥 <b>Players ({len(registrations)}/{table['max_players']}):</b>\n"

        if not registrations:
            message += "   <i>No players registered yet</i>\n"
        else:
            for i, player in enumerate(registrations, 1):
                # Build player name
                player_name_parts = []
                first_name = row_get(player, "first_name")
                last_name = row_get(player, "last_name")

                if first_name:
                    player_name_parts.append(first_name)
                if last_name:
                    player_name_parts.append(last_name)

                player_name = (
                    " ".join(player_name_parts) if player_name_parts else "Unknown"
                )

                # Add username if available
                username = row_get(player, "username")
                username_str = f"(@{username})" if username else "(no username)"

                message += f"   {i}. {player_name} {username_str}\n"

        # Available slots
        remaining_slots = table["max_players"] - len(registrations)
        if remaining_slots > 0:
            message += f"\n🟢 <b>{remaining_slots} slot{'s' if remaining_slots != 1 else ''} available</b>"
        else:
            message += "\n🔴 <b>Table is full</b>"

        await safe_edit_message(query, message)
        await query.answer()

    except Exception as e:
        logger.error(f"Error in show_players_callback: {e}", exc_info=True)
        await query.answer(
            text="❌ An error occurred. Please try again.", show_alert=True
        )


def tables_handler() -> CommandHandler:
    """Returns the tables command handler."""
    return CommandHandler("tables", tables)
