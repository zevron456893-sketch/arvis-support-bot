from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import SERVERS, CATEGORIES

def main_menu():
    return ReplyKeyboardMarkup([
        ["👤 Мій профіль", "🎫 Створити звернення"],
        ["📋 Мої звернення", "ℹ️ Інформація"],
    ], resize_keyboard=True)

def servers():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s, callback_data=f"profile:server:{i}")]
        for i, s in enumerate(SERVERS)
    ])

def confirm_profile():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Все правильно", callback_data="profile:confirm")],
        [InlineKeyboardButton("✏️ Змінити дані", callback_data="profile:edit")],
    ])

def profile_actions():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Змінити сервер", callback_data="profile:change:server")],
        [InlineKeyboardButton("🆔 Змінити номер аккаунта", callback_data="profile:change:account")],
        [InlineKeyboardButton("👤 Змінити нікнейм", callback_data="profile:change:nickname")],
        [InlineKeyboardButton("🎫 Мої звернення", callback_data="user:tickets")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="user:back")],
    ])

def categories():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"ticket:category:{key}")]
        for key, label in CATEGORIES
    ])

def ticket_list(rows):
    buttons = []
    for row in rows:
        buttons.append([
            InlineKeyboardButton(
                f"{row['ticket_number']} — { {'new':'🟡','working':'🟢','closed':'🔴'}[row['status']] }",
                callback_data=f"user:ticket:{row['id']}"
            )
        ])
    return InlineKeyboardMarkup(buttons) if buttons else None

def back():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="user:back")]])
