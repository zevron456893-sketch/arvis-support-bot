from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Нові звернення", callback_data="admin:list:new")],
        [InlineKeyboardButton("🔄 В роботі", callback_data="admin:list:working")],
        [InlineKeyboardButton("✅ Закриті", callback_data="admin:list:closed")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton("🔎 Пошук тикета", callback_data="admin:search")],
        [InlineKeyboardButton("👥 Адміністратори", callback_data="admin:admins")],
    ])

def ticket_actions(ticket_id, status):
    rows = []
    if status == "new":
        rows.append([InlineKeyboardButton("🟢 Взяти в роботу", callback_data=f"admin:take:{ticket_id}")])
    if status != "closed":
        rows.append([InlineKeyboardButton("💬 Відповісти", callback_data=f"admin:reply:{ticket_id}")])
        rows.append([InlineKeyboardButton("🔴 Закрити", callback_data=f"admin:close:{ticket_id}")])
    rows.append([InlineKeyboardButton("📋 Історія", callback_data=f"admin:history:{ticket_id}")])
    rows.append([InlineKeyboardButton("⬅️ Панель", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)

def ticket_list(rows):
    buttons = []
    for row in rows:
        icon = {"new":"🟡","working":"🟢","closed":"🔴"}[row["status"]]
        buttons.append([InlineKeyboardButton(
            f"{icon} {row['ticket_number']} — {row['nickname'][:24]}",
            callback_data=f"admin:view:{row['id']}"
        )])
    buttons.append([InlineKeyboardButton("⬅️ Панель", callback_data="admin:menu")])
    return InlineKeyboardMarkup(buttons)

def search_cancel():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Панель", callback_data="admin:menu")]])

def admin_list():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Панель", callback_data="admin:menu")]])
