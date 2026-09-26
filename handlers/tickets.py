from telegram import Update
from telegram.ext import ContextTypes
from database import get_user, profile_complete, create_ticket, list_user_tickets, get_ticket, get_messages
from config import CATEGORY_LABELS, STATUS_LABELS
from keyboards.user import categories, ticket_list, main_menu, back
from services.ticket_service import ticket_history_text
from services.message_service import save_incoming
from handlers.admin import notify_new_ticket

async def create_start(update, context):
    user = get_user(update.effective_user.id)
    if not profile_complete(user):
        context.user_data["profile_mode"] = "server"
        from keyboards.user import servers
        await update.message.reply_text("🌐 Виберіть сервер", reply_markup=servers())
        return
    await update.message.reply_text("📁 Виберіть категорію звернення:", reply_markup=categories())

async def category_callback(update, context):
    q = update.callback_query
    await q.answer()
    category = q.data.split(":")[-1]
    ticket = create_ticket(q.from_user.id, category)
    context.user_data["active_ticket_id"] = ticket["id"]
    await q.edit_message_text(
        f"🎫 Ваше звернення {ticket['ticket_number']} створено.\n\n"
        f"Категорія: {CATEGORY_LABELS[category]}\n\n"
        "Опишіть вашу проблему максимально детально.\n\n"
        "Ви також можете надіслати фотографію, відео або документ."
    )
    await notify_new_ticket(context, ticket)

async def my_tickets(update, context):
    rows = list_user_tickets(update.effective_user.id)
    if not rows:
        await update.message.reply_text("📋 У вас ще немає звернень.", reply_markup=main_menu())
        return
    await update.message.reply_text("📋 Мої звернення:", reply_markup=ticket_list(rows))

async def user_ticket_callback(update, context):
    q = update.callback_query
    await q.answer()
    ticket_id = int(q.data.split(":")[-1])
    ticket = get_ticket(ticket_id)
    if not ticket or ticket["telegram_id"] != q.from_user.id:
        await q.answer("Тикет недоступний.", show_alert=True)
        return
    await q.edit_message_text(ticket_history_text(ticket_id), reply_markup=back())

async def user_back(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("🎮 ARVIS ONLINE SUPPORT")
    await q.message.reply_text("Оберіть дію:", reply_markup=main_menu())
