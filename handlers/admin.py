from telegram import Update
from telegram.ext import ContextTypes
from database import (
    is_admin, get_ticket, set_ticket_working, close_ticket, list_tickets,
    stats, search_tickets, list_admins, add_admin, remove_admin,
    set_admin_session, clear_admin_session, get_messages
)
from config import CATEGORY_LABELS, STATUS_LABELS
from keyboards.admin import admin_menu, ticket_actions, ticket_list, search_cancel, admin_list
from services.ticket_service import ticket_admin_text, ticket_history_text

def _admin_ids():
    from config import ADMIN_IDS
    return list(ADMIN_IDS)

async def notify_new_ticket(context, ticket):
    text = ticket_admin_text(ticket)
    for admin_id in _admin_ids():
        try:
            await context.bot.send_message(
                admin_id, text, reply_markup=ticket_actions(ticket["id"], ticket["status"])
            )
        except Exception:
            pass

async def forward_to_admins(context, ticket, message):
    for admin_id in _admin_ids():
        try:
            await context.bot.send_message(
                admin_id,
                f"💬 Нове повідомлення у {ticket['ticket_number']} від гравця."
            )
            await context.bot.copy_message(
                chat_id=admin_id,
                from_chat_id=message.chat_id,
                message_id=message.message_id,
            )
        except Exception:
            pass

async def admin_entry(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Немає доступу.")
        return
    await update.message.reply_text("🛠 ПАНЕЛЬ ПІДТРИМКИ", reply_markup=admin_menu())

async def admin_callback(update, context):
    q = update.callback_query
    if not is_admin(q.from_user.id):
        await q.answer("Немає доступу.", show_alert=True)
        return
    await q.answer()
    data = q.data.split(":")
    action = data[1]
    if action == "menu":
        clear_admin_session(q.from_user.id)
        await q.edit_message_text("🛠 ПАНЕЛЬ ПІДТРИМКИ", reply_markup=admin_menu())
        return
    if action == "list":
        status = data[2]
        rows = list_tickets(status)
        title = {"new":"📥 Нові звернення","working":"🔄 В роботі","closed":"✅ Закриті"}[status]
        await q.edit_message_text(f"{title}\n\nЗнайдено: {len(rows)}", reply_markup=ticket_list(rows))
        return
    if action == "view":
        ticket = get_ticket(int(data[2]))
        if not ticket:
            await q.edit_message_text("Тикет не знайдено.", reply_markup=admin_menu())
            return
        await q.edit_message_text(
            ticket_admin_text(ticket),
            reply_markup=ticket_actions(ticket["id"], ticket["status"])
        )
        return
    if action == "take":
        ticket_id = int(data[2])
        ticket = set_ticket_working(ticket_id, q.from_user.id)
        if not ticket:
            await q.answer("Тикет уже взятий у роботу або закритий.", show_alert=True)
            return
        await q.edit_message_text(
            ticket_admin_text(ticket) + f"\n\n🛠 Оператор: {q.from_user.id}",
            reply_markup=ticket_actions(ticket_id, "working")
        )
        try:
            await context.bot.send_message(
                ticket["telegram_id"],
                f"👨‍💻 Ваше звернення {ticket['ticket_number']} взято в роботу оператором.\n\nОчікуйте відповіді."
            )
        except Exception:
            pass
        return
    if action == "reply":
        ticket = get_ticket(int(data[2]))
        if not ticket or ticket["status"] == "closed":
            await q.answer("Тикет закритий.", show_alert=True)
            return
        set_admin_session(q.from_user.id, ticket["id"])
        await q.message.reply_text(
            f"💬 Режим відповіді для {ticket['ticket_number']} увімкнено.\n"
            "Надішліть наступне повідомлення (текст, фото, відео або документ)."
        )
        return
    if action == "close":
        ticket = close_ticket(int(data[2]), q.from_user.id)
        if not ticket:
            await q.answer("Тикет уже закритий.", show_alert=True)
            return
        await q.edit_message_text(
            ticket_admin_text(ticket),
            reply_markup=admin_menu()
        )
        try:
            await context.bot.send_message(
                ticket["telegram_id"],
                f"✅ Ваше звернення {ticket['ticket_number']} було закрито.\n\n"
                "Дякуємо за звернення до Arvis Online Support!"
            )
        except Exception:
            pass
        return
    if action == "history":
        await q.edit_message_text(
            ticket_history_text(int(data[2])),
            reply_markup=ticket_actions(int(data[2]), get_ticket(int(data[2]))["status"])
        )
        return
    if action == "stats":
        total, statuses, by_admin, by_cat, avg = stats()
        lines = [
            "📊 СТАТИСТИКА",
            "",
            f"Всього тикетів: {total}",
            f"🟡 Нових: {statuses['new']}",
            f"🟢 В роботі: {statuses['working']}",
            f"🔴 Закритих: {statuses['closed']}",
            "",
            "🛠 За операторами:"
        ]
        lines += [f"• {r['admin']}: {r['n']}" for r in by_admin]
        lines += ["", "📁 За категоріями:"]
        lines += [f"• {CATEGORY_LABELS.get(r['category'], r['category'])}: {r['n']}" for r in by_cat]
        if avg is not None:
            lines += ["", f"⏱ Середній час до закриття: {avg/3600:.2f} год."]
        await q.edit_message_text("\n".join(lines), reply_markup=admin_menu())
        return
    if action == "search":
        context.user_data["admin_search"] = True
        await q.edit_message_text(
            "🔎 Надішліть номер тикета, Telegram ID, нікнейм, номер аккаунта або сервер.",
            reply_markup=search_cancel()
        )
        return
    if action == "admins":
        rows = list_admins()
        text = "👥 АДМІНІСТРАТОРИ\n\n" + "\n".join(
            f"• {r['telegram_id']} — {r['role']}" for r in rows
        )
        await q.edit_message_text(text, reply_markup=admin_list())

async def admin_search_message(update, context):
    if not is_admin(update.effective_user.id) or not context.user_data.get("admin_search"):
        return False
    query = (update.message.text or "").strip()
    rows = search_tickets(query)
    context.user_data.pop("admin_search", None)
    if not rows:
        await update.message.reply_text("🔎 Нічого не знайдено.", reply_markup=admin_menu())
        return True
    await update.message.reply_text("🔎 Результати пошуку:", reply_markup=ticket_list(rows))
    return True
