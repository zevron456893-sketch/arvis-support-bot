import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from config import BOT_TOKEN
from database import init_db, is_admin
from handlers.start import start
from handlers.profile import (
    show_profile, profile_start, server_callback, profile_text,
    confirm, edit, profile_change, profile_change_text
)
from handlers.tickets import create_start, category_callback, my_tickets, user_ticket_callback, user_back
from handlers.admin import admin_entry, admin_callback, admin_search_message
from handlers.messages import user_message, admin_message
from keyboards.user import main_menu

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("arvis-support")

async def information(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Arvis Online Support\n\n"
        "Цей бот призначений для технічної підтримки гравців Arvis Online.\n\n"
        "1. Заповніть профіль.\n"
        "2. Створіть звернення та виберіть категорію.\n"
        "3. Надішліть опис і, за потреби, фото/відео/документи.\n"
        "4. Оператор відповість у цьому ж тикеті."
    )

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    text = update.message.text or ""

    # Admin message modes take priority.
    if await admin_search_message(update, context):
        return
    if await admin_message(update, context):
        return

    # Profile input.
    if await profile_text(update, context):
        return
    if await profile_change_text(update, context):
        return

    # User ticket messages.
    if await user_message(update, context):
        return

    # Main menu.
    if text == "👤 Мій профіль":
        await show_profile(update, context)
    elif text == "🎫 Створити звернення":
        await create_start(update, context)
    elif text == "📋 Мої звернення":
        await my_tickets(update, context)
    elif text == "ℹ️ Інформація":
        await information(update, context)
    elif text == "🛠 ПАНЕЛЬ ПІДТРИМКИ" and is_admin(update.effective_user.id):
        await admin_entry(update, context)
    else:
        await update.message.reply_text(
            "Оберіть дію з меню або спочатку створіть/відкрийте звернення.",
            reply_markup=main_menu()
        )

async def media_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    if await admin_message(update, context):
        return
    await user_message(update, context)

def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN не заданий. Створіть .env на основі .env.example і додайте токен."
        )
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_entry))

    app.add_handler(CallbackQueryHandler(server_callback, pattern=r"^profile:server:\d+$"))
    app.add_handler(CallbackQueryHandler(confirm, pattern=r"^profile:confirm$"))
    app.add_handler(CallbackQueryHandler(edit, pattern=r"^profile:edit$"))
    app.add_handler(CallbackQueryHandler(profile_change, pattern=r"^profile:change:(server|account|nickname)$"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^ticket:category:"))
    app.add_handler(CallbackQueryHandler(user_ticket_callback, pattern=r"^user:ticket:\d+$"))
    app.add_handler(CallbackQueryHandler(user_back, pattern=r"^user:back$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.ANIMATION | filters.AUDIO),
        media_router
    ))

    logger.info("Arvis Online Support starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
