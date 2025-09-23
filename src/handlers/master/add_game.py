# src/handlers/master.py

"""
Command handlers for masters.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.models import user as user_model
from src.models import table as table_model
from src.utils.decorators import master_required
from src.utils.telegram_helpers import cancel

logger = logging.getLogger(__name__)

# States for ConversationHandler
GAME, NAME, MAX_PLAYERS, DESCRIPTION, IMAGE, NUM_SESSIONS = range(6)


@master_required
async def add_one_shot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the one-shot creation conversation."""
    context.user_data["type"] = "one_shot"
    await update.message.reply_text(
        "Let's add a new one-shot. What is the name of the game?"
    )
    return GAME


@master_required
async def add_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the campaign creation conversation."""
    context.user_data["type"] = "campaign"
    await update.message.reply_text(
        "Let's add a new campaign. What is the name of the game?"
    )
    return GAME


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the name table and asks for the max number of players."""
    context.user_data["game"] = update.message.text
    await update.message.reply_text("What’s the name of your table?")
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the game name and asks for the max number of players."""
    context.user_data["name"] = update.message.text
    await update.message.reply_text("How many players can join? (including the master)")
    return MAX_PLAYERS


async def max_players(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the max number of players and asks for the description."""
    context.user_data["max_players"] = int(update.message.text)
    await update.message.reply_text("Provide a brief description of the adventure.")
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the description and asks for an image."""
    context.user_data["description"] = update.message.text
    await update.message.reply_text(
        "Do you want to add an image? (Send the image or /skip)"
    )
    return IMAGE


async def image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the image and asks for the number of sessions if it's a campaign."""
    context.user_data["image"] = update.message.photo[-1].file_id
    if context.user_data.get("type") == "campaign":
        await update.message.reply_text("How many sessions are planned?")
        return NUM_SESSIONS
    else:
        await save_table(update, context)
        return ConversationHandler.END


async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the image and asks for the number of sessions if it's a campaign."""
    context.user_data["image"] = None
    if context.user_data.get("type") == "campaign":
        await update.message.reply_text("How many sessions are planned?")
        return NUM_SESSIONS
    else:
        await save_table(update, context)
        return ConversationHandler.END


async def num_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the number of sessions and saves the table."""
    context.user_data["num_sessions"] = int(update.message.text)
    await save_table(update, context)
    return ConversationHandler.END


async def save_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saves the table to the database."""
    user = user_model.get_user(update.effective_user.id)
    table_model.create_table(
        master_id=user["telegram_id"],
        type=context.user_data["type"],
        game=context.user_data["game"],
        name=context.user_data["name"],
        max_players=context.user_data["max_players"],
        description=context.user_data["description"],
        image=context.user_data.get("image"),
        num_sessions=context.user_data.get("num_sessions"),
    )
    await update.message.reply_text("Table created successfully!")


@master_required
async def pause_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a list of active campaigns to pause."""
    user = user_model.get_user(update.effective_user.id)
    campaigns = table_model.get_active_campaigns_by_master(user["telegram_id"])

    if not campaigns:
        await update.message.reply_text("You have no active campaigns to pause.")
        return

    keyboard = []
    for campaign in campaigns:
        keyboard.append(
            [
                InlineKeyboardButton(
                    campaign["game"], callback_data=f"pause_{campaign['id']}"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select a campaign to pause:", reply_markup=reply_markup
    )


async def pause_campaign_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles the pause campaign callback."""
    query = update.callback_query
    table_id = int(query.data.split("_")[1])

    table_model.update_table_status(table_id, False)

    await query.answer("Campaign paused.")
    await query.edit_message_text(text="Campaign has been paused.")


@master_required
async def continue_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a list of inactive campaigns to continue."""
    user = user_model.get_user(update.effective_user.id)
    campaigns = table_model.get_inactive_campaigns_by_master(user["telegram_id"])

    if not campaigns:
        await update.message.reply_text("You have no inactive campaigns to continue.")
        return

    keyboard = []
    for campaign in campaigns:
        keyboard.append(
            [
                InlineKeyboardButton(
                    campaign["game"], callback_data=f"continue_{campaign['id']}"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select a campaign to continue:", reply_markup=reply_markup
    )


async def continue_campaign_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles the continue campaign callback."""
    query = update.callback_query
    table_id = int(query.data.split("_")[1])

    table_model.update_table_status(table_id, True)

    await query.answer("Campaign continued.")
    await query.edit_message_text(text="Campaign has been continued.")


def add_one_shot_handler() -> ConversationHandler:
    """Returns the add one-shot conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("addOneShot", add_one_shot)],
        states={
            GAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, game)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            MAX_PLAYERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_players)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            IMAGE: [
                MessageHandler(filters.PHOTO, image),
                CommandHandler("skip", skip_image),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


def add_campaign_handler() -> ConversationHandler:
    """Returns the add campaign conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("addCampaign", add_campaign)],
        states={
            GAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, game)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            MAX_PLAYERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_players)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            IMAGE: [
                MessageHandler(filters.PHOTO, image),
                CommandHandler("skip", skip_image),
            ],
            NUM_SESSIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, num_sessions)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


def pause_campaign_handler() -> CommandHandler:
    """Returns the pause campaign command handler."""
    return CommandHandler("pauseCampaign", pause_campaign)


def continue_campaign_handler() -> CommandHandler:
    """Returns the continue campaign command handler."""
    return CommandHandler("continueCampaign", continue_campaign)
