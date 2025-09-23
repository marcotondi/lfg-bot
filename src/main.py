# src/main.py

"""
Main entry point for the Telegram bot.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.handlers.common import mute, start, tables, commands
from src.handlers.admin import (
    admin_tables,
    publish_tables,
    admin_edit_table,
    role_management,
)
from src.handlers.master import master_edit, add_game, master_my_tables
from src.config import TELEGRAM_TOKEN
from src.database import init_db

# --- Logging Configuration ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 1. Get the root logger
log = logging.getLogger()
log.setLevel(logging.INFO)  # Set the minimum level for the root logger

# 2. Create a formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# 3. Create a timed rotating file handler for daily logs
file_handler = TimedRotatingFileHandler(
    os.path.join(LOG_DIR, "bot.log"), when="midnight", backupCount=7, encoding="utf-8"
)
file_handler.setFormatter(formatter)

# 4. Create a stream handler to print logs to the console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# 5. Add handlers to the root logger
log.addHandler(file_handler)
log.addHandler(stream_handler)

logger = logging.getLogger(__name__)
# --- End of Logging Configuration ---


def main() -> None:
    """Start the telegram bot."""
    # Initialize the database
    init_db()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(start.start_handler())
    application.add_handler(tables.tables_handler())
    application.add_handler(mute.mute_handler())
    application.add_handler(commands.commands_handler())

    application.add_handler(add_game.add_one_shot_handler())
    application.add_handler(add_game.add_campaign_handler())
    application.add_handler(add_game.pause_campaign_handler())
    application.add_handler(add_game.continue_campaign_handler())
    application.add_handler(master_my_tables.my_tables_handler())
    application.add_handler(master_edit.master_edit_handler())

    application.add_handler(admin_tables.tables_handler())
    application.add_handler(publish_tables.publish_tables_handler())
    application.add_handler(role_management.set_master_handler())
    application.add_handler(role_management.unset_master_handler())
    application.add_handler(role_management.set_admin_handler())
    application.add_handler(role_management.unset_admin_handler())

    application.add_handler(
        CallbackQueryHandler(add_game.pause_campaign_callback, pattern="^pause_")
    )
    application.add_handler(
        CallbackQueryHandler(add_game.continue_campaign_callback, pattern="^continue_")
    )
    application.add_handler(
        CallbackQueryHandler(tables.join_table_callback, pattern="^join_")
    )
    application.add_handler(
        CallbackQueryHandler(tables.unjoin_table_callback, pattern="^unjoin_")
    )
    application.add_handler(
        CallbackQueryHandler(tables.show_players_callback, pattern="^show_")
    )

    edit_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_edit_table.edit_table_callback, pattern="^edit_")
        ],
        states={
            0: [
                CallbackQueryHandler(
                    admin_edit_table.edit_choice,
                    pattern="^(edit_description|edit_max_players)$",
                )
            ],
            1: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, admin_edit_table.edit_value
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_edit_table.cancel)],
    )
    application.add_handler(edit_conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
