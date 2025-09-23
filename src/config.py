"""
Configuration settings and constants for the bot.
"""

import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN non trovato nelle variabili d'ambiente")

# Database file
DB_FILE = os.getenv('DB_FILE', 'src.db')  # Default fallback

# Environment setting (opzionale)
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Validazione configurazione
def validate_config():
    """Valida che tutte le configurazioni necessarie siano presenti."""
    required_vars = ['TELEGRAM_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Variabili d'ambiente mancanti: {', '.join(missing_vars)}")
    
    print(f"✓ Configurazione caricata correttamente (Environment: {ENVIRONMENT})")

# Chiamata automatica della validazione
if __name__ == "__main__":
    validate_config()