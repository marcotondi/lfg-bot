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

from src.config import TELEGRAM_TOKEN
from src.database import init_db
from src.handlers import common, master, admin

# --- Logging Configuration ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 1. Get the root logger
log = logging.getLogger()
log.setLevel(logging.INFO) # Set the minimum level for the root logger

# 2. Create a formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 3. Create a timed rotating file handler for daily logs
file_handler = TimedRotatingFileHandler(
    os.path.join(LOG_DIR, 'bot.log'),
    when='midnight',
    backupCount=7,
    encoding='utf-8'
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
    application.add_handler(common.start_handler())
    application.add_handler(common.tables_handler())
    application.add_handler(common.mute_handler())
    application.add_handler(common.commands_handler())

    application.add_handler(master.add_one_shot_handler())
    application.add_handler(master.add_campaign_handler())
    application.add_handler(master.pause_campaign_handler())
    application.add_handler(master.continue_campaign_handler())
    application.add_handler(master.my_tables_handler())
    application.add_handler(master.master_edit_handler())
    
    application.add_handler(admin.tables_handler())
    application.add_handler(admin.publish_tables_handler())
    application.add_handler(admin.set_master_handler())
    application.add_handler(admin.unset_master_handler())
    application.add_handler(admin.set_admin_handler())
    application.add_handler(admin.unset_admin_handler())

    application.add_handler(CallbackQueryHandler(master.pause_campaign_callback, pattern='^pause_'))
    application.add_handler(CallbackQueryHandler(common.join_table_callback, pattern='^join_'))
    application.add_handler(CallbackQueryHandler(common.unjoin_table_callback, pattern='^unjoin_'))
    application.add_handler(CallbackQueryHandler(common.show_players_callback, pattern='^show_'))

    edit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin.edit_table_callback, pattern='^edit_')],
        states={
            0: [CallbackQueryHandler(admin.edit_choice, pattern='^(edit_description|edit_max_players)$')],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.edit_value)],
        },
        fallbacks=[CommandHandler("cancel", admin.cancel)],
    )
    application.add_handler(edit_conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()