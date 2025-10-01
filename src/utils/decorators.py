# src/utils/decorators.py

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from src.models import user as user_model

def admin_required(func):
    """Decorator to check if the user is an admin."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = user_model.get_telegram_user(update.effective_user.id)
        if not user or not user['is_admin']:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def master_required(func):
    """Decorator to check if the user is a master."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = user_model.get_telegram_user(update.effective_user.id)
        if not user or not user['is_master']:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
