from config import CATEGORY_LABELS, STATUS_LABELS
from database import get_ticket, get_messages

def ticket_header(ticket):
    return (
        f"🎫 {ticket['ticket_number']}\n\n"
        f"👤 Нікнейм: {ticket['nickname']}\n"
        f"🆔 Аккаунт: {ticket['account_id']}\n"
        f"🌐 Сервер: {ticket['server']}\n"
        f"📱 Telegram: @{ticket['username']}" if ticket['username'] else
        f"📱 Telegram: —"
    )

def ticket_admin_text(ticket, first_message=None):
    category = CATEGORY_LABELS.get(ticket["category"], ticket["category"])
    msg = first_message or ""
    return (
        "━━━━━━━━━━━━━━━━\n"
        "🎫 НОВЕ ЗВЕРНЕННЯ\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"{ticket['ticket_number']}\n\n"
        f"👤 Нікнейм: {ticket['nickname']}\n"
        f"🆔 Аккаунт: {ticket['account_id']}\n"
        f"🌐 Сервер: {ticket['server']}\n\n"
        f"📱 Telegram: @{ticket['username'] or '—'}\n"
        f"🔢 Telegram ID: {ticket['telegram_id']}\n\n"
        f"📁 Категорія:\n{category}\n\n"
        f"💬 Повідомлення:\n{msg or '—'}\n\n"
        f"📊 Статус: {STATUS_LABELS[ticket['status']]}"
    )

def ticket_history_text(ticket_id):
    ticket = get_ticket(ticket_id)
    messages = get_messages(ticket_id)
    if not ticket:
        return "Тикет не знайдено."
    lines = [
        f"🎫 {ticket['ticket_number']}",
        f"📁 {CATEGORY_LABELS.get(ticket['category'], ticket['category'])}",
        f"📊 {STATUS_LABELS.get(ticket['status'], ticket['status'])}",
        f"🕐 Створено: {ticket['created_at']}",
        f"🛠 Оператор: {ticket['admin_id'] or 'не призначено'}",
        "",
        "💬 ІСТОРІЯ"
    ]
    for m in messages:
        sender = "👤 Гравець" if m["sender_type"] == "user" else "🛠 Оператор"
        body = m["text"] or f"[{m['message_type']}]"
        lines.append(f"{sender} • {m['created_at']}\n{body}")
    result = "\n".join(lines)
    # Telegram text messages have a size limit; keep history readable in one message.
    if len(result) > 3800:
        result = result[:3700] + "\n\n… Історію обрізано. Зверніться до оператора для повного журналу."
    return result
