# src/handlers/admin/role_management.py

"""
Command handlers for admins to manage user roles (admin, master).
"""

import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.models import user as user_model
from src.utils.decorators import admin_required

logger = logging.getLogger(__name__)


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
