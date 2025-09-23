# src/handlers/common/commands.py

"""
Common command handlers for all users.
"""

import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.models import user as user_model

logger = logging.getLogger(__name__)


async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the available commands based on user role."""
    message = update.message
    if not message:
        return

    user = user_model.get_user(update.effective_user.id)

    response_message = "📋 <b>Available commands:</b>\n\n"

    # Common commands
    response_message += "👤 <b>User commands:</b>\n"
    response_message += "• /start - Start the bot\n"
    response_message += "• /tables - Show active tables\n"
    response_message += "• /mute - Mute/unmute notifications\n"
    response_message += "• /commands - Show this message\n\n"

    # Master commands
    if user and user["is_master"]:
        response_message += "🎭 <b>Master commands:</b>\n"
        response_message += "• /addOneShot - Add a new one-shot table\n"
        response_message += "• /addCampaign - Add a new campaign table\n"
        response_message += "• /mytables - Show and edit your tables\n"
        response_message += "• /pauseCampaign - Pause a campaign\n"
        response_message += "• /continueCampaign - Continue a campaign\n\n"

    # Admin commands
    if user and user["is_admin"]:
        response_message += "⚙️ <b>Admin commands:</b>\n"
        response_message += "• /tables - Review and edit all tables\n"
        response_message += "• /publishTables - Publish tables to users\n"
        response_message += "• /setMaster &lt;user_id&gt; - Set a user as master\n"
        response_message += "• /unsetMaster &lt;user_id&gt; - Unset a user as master\n"
        response_message += "• /setAdmin &lt;user_id&gt; - Set a user as admin\n"
        response_message += "• /unsetAdmin &lt;user_id&gt; - Unset a user as admin\n"

    await message.reply_html(response_message)


def commands_handler() -> CommandHandler:
    """Returns the commands command handler."""
    return CommandHandler("commands", commands)
