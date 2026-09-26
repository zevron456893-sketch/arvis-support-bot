from telegram import Update
from telegram.ext import ContextTypes
from database import get_ticket, add_message, get_admin_session, is_admin, get_user, get_latest_active_ticket
from services.message_service import save_incoming

async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Profile input is handled before this function by the main dispatcher.
    ticket_id = context.user_data.get("active_ticket_id")
    ticket = get_ticket(ticket_id) if ticket_id else None
    if not ticket:
        ticket = get_latest_active_ticket(update.effective_user.id)
        if ticket:
            context.user_data["active_ticket_id"] = ticket["id"]
    if not ticket:
        return False
    if not ticket or ticket["telegram_id"] != update.effective_user.id:
        return False
    if ticket["status"] == "closed":
        context.user_data.pop("active_ticket_id", None)
        await update.message.reply_text(
            "🔴 Це звернення вже закрито. Створіть нове звернення для продовження."
        )
        return True
    save_incoming(update.message, ticket_id, "user")
    from handlers.admin import forward_to_admins
    await forward_to_admins(context, ticket, update.message)
    return True

async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return False
    session = get_admin_session(update.effective_user.id)
    if not session or not session["ticket_id"]:
        return False
    ticket = get_ticket(session["ticket_id"])
    if not ticket or ticket["status"] == "closed":
        await update.message.reply_text("Активний тикет для відповіді не вибрано.")
        return True
    save_incoming(update.message, ticket["id"], "admin")
    try:
        await context.bot.copy_message(
            chat_id=ticket["telegram_id"],
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
        await update.message.reply_text(f"✅ Повідомлення надіслано гравцю {ticket['ticket_number']}.")
    except Exception as exc:
        await update.message.reply_text(f"Не вдалося доставити повідомлення: {exc}")
    return True
