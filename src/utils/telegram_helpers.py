from telegram import Message
from telegram.ext import CallbackContext
from telegram.error import TelegramError


async def safe_edit_message(query, new_text: str, parse_mode: str = "HTML"):
    """
    Edita in sicurezza un messaggio Telegram, gestendo automaticamente
    i casi text / caption / inaccessibile.

    :param query: CallbackQuery ricevuta dall'update
    :param new_text: Nuovo contenuto (stringa)
    :param parse_mode: Formattazione (default: HTML)
    """
    msg = query.message

    # Controllo se è un messaggio accessibile
    if not isinstance(msg, Message):
        await query.answer("Messaggio non accessibile", show_alert=True)
        return

    try:
        if msg.text is not None:
            await query.edit_message_text(text=new_text, parse_mode=parse_mode)
        elif msg.caption is not None:
            await query.edit_message_caption(caption=new_text, parse_mode=parse_mode)
        else:
            await query.answer("Il messaggio non ha né testo né caption", show_alert=True)
    except TelegramError as e:
        # Logga e notifica in caso di errore API
        print(f"Errore durante safe_edit_message: {e}")
        await query.answer("Errore nella modifica del messaggio", show_alert=True)
