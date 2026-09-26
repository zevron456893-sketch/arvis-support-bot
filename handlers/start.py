from telegram import Update
from telegram.ext import ContextTypes
from database import upsert_user, is_admin
from keyboards.user import main_menu
from keyboards.admin import admin_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    text = (
        "🎮 ARVIS ONLINE SUPPORT\n\n"
        "«Вітаємо у службі підтримки Arvis Online!\n\n"
        "Перед створенням звернення заповніть дані свого ігрового акаунта.»"
    )
    await update.message.reply_text(text, reply_markup=main_menu())
    if is_admin(update.effective_user.id):
        await update.message.reply_text("🛠 ПАНЕЛЬ ПІДТРИМКИ", reply_markup=admin_menu())
