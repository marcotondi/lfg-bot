# src/handlers/master.py

"""
Command handlers for masters.
"""

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
    await update.message.reply_text("Do you want to add an image? (Send the image or /skip)")
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
        master_id=user["id"],
        type=context.user_data["type"],
        game=context.user_data["game"],
        name=context.user_data["name"],
        max_players=context.user_data["max_players"],
        description=context.user_data["description"],
        image=context.user_data.get("image"),
        num_sessions=context.user_data.get("num_sessions"),
    )
    await update.message.reply_text("Table created successfully!")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Table creation cancelled.")
    return ConversationHandler.END


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

TABLE_ID = range(6)

@master_required
async def pause_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a list of active campaigns to pause."""
    user = user_model.get_user(update.effective_user.id)
    campaigns = table_model.get_active_campaigns_by_master(user["id"])

    if not campaigns:
        await update.message.reply_text("You have no active campaigns to pause.")
        return

    keyboard = []
    for campaign in campaigns:
        keyboard.append([InlineKeyboardButton(campaign["game"], callback_data=f"pause_{campaign['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a campaign to pause:", reply_markup=reply_markup)

async def pause_campaign_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the pause campaign callback."""
    query = update.callback_query
    table_id = int(query.data.split("_")[1])
    
    table_model.update_table_status(table_id, False)
    
    await query.answer("Campaign paused.")
    await query.edit_message_text(text=f"Campaign has been paused.")

def pause_campaign_handler() -> CommandHandler:
    """Returns the pause campaign command handler."""
    return CommandHandler("pauseCampaign", pause_campaign)

# FIXME: GESTIRE IL CONTINUE COMAPGNA COME IL PAUSA
@master_required
async def continue_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the continue campaign conversation."""
    await update.message.reply_text("Please send the ID of the campaign you want to continue.")
    return TABLE_ID


async def get_table_id_and_continue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Continues a campaign."""
    table_id = int(update.message.text)
    table = table_model.get_table_by_id(table_id)
    user = user_model.get_user(update.effective_user.id)
    if table and table["master_id"] == user["id"]:
        table_model.update_table_status(table_id, True)
        await update.message.reply_text("Campaign continued.")
    else:
        await update.message.reply_text("Table not found or you are not the master.")
    return ConversationHandler.END

def continue_campaign_handler() -> ConversationHandler:
    """Returns the continue campaign conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("continueCampaign", continue_campaign)],
        states={
            TABLE_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_table_id_and_continue
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


# Conversation states for editing
EDIT_CHOICE, EDIT_VALUE = range(7, 9)

@master_required
async def my_tables(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a list of the master's tables with edit buttons."""
    user = user_model.get_user(update.effective_user.id)
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

@master_required
async def edit_table_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the master edit table callback, ensuring ownership."""
    query = update.callback_query
    table_id = int(query.data.split("_")[2]) # e.g., master_edit_123
    
    # Security Check: Ensure the user is the master of this table
    user = user_model.get_user(update.effective_user.id)
    table = table_model.get_table_by_id(table_id)
    if not table or table["master_id"] != user["id"]:
        await query.answer("You are not authorized to edit this table.", show_alert=True)
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
    await query.edit_message_text(text=f"Please send the new {query.data.split('_')[1]}.")
    return EDIT_VALUE

@master_required
async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Updates the table with the new value."""
    table_id = context.user_data["table_id"]
    edit_choice = context.user_data["edit_choice"]
    new_value = update.message.text
    table = table_model.get_table_by_id(table_id)

    # Security check is implicitly handled by the entry point, but good practice
    user = user_model.get_user(update.effective_user.id)
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


def my_tables_handler() -> CommandHandler:
    """Returns the /mytables command handler."""
    return CommandHandler("mytables", my_tables)

def master_edit_handler() -> ConversationHandler:
    """Returns the master edit conversation handler."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_table_callback, pattern='^master_edit_')],
        states={
            EDIT_CHOICE: [CallbackQueryHandler(edit_choice, pattern='^(edit_description|edit_max_players)')],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )