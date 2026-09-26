from telegram import Update
from telegram.ext import ContextTypes
from database import upsert_user, get_user, update_profile, profile_complete
from config import SERVERS
from keyboards.user import servers, confirm_profile, profile_actions, main_menu

async def show_profile(update, context):
    user = get_user(update.effective_user.id)
    if not user or not profile_complete(user):
        await update.message.reply_text("Спочатку заповніть профіль через «🎫 Створити звернення».")
        return
    await update.message.reply_text(
        f"👤 Ваш профіль\n\n🌐 Сервер: {user['server']}\n"
        f"🆔 Аккаунт: {user['account_id']}\n👤 Нікнейм: {user['nickname']}",
        reply_markup=profile_actions()
    )

async def profile_start(update, context):
    upsert_user(update.effective_user)
    user = get_user(update.effective_user.id)
    if profile_complete(user):
        return await show_profile(update, context)
    context.user_data["profile_mode"] = "server"
    await update.message.reply_text("🌐 Виберіть сервер", reply_markup=servers())

async def server_callback(update, context):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.rsplit(":", 1)[1])
    selected = SERVERS[idx]
    mode = context.user_data.get("profile_mode")

    if mode == "change_server":
        update_profile(q.from_user.id, server=selected)
        context.user_data.pop("profile_mode", None)
        user = get_user(q.from_user.id)
        await q.edit_message_text(
            f"✅ Сервер оновлено.\n\n🌐 Сервер: {user['server']}\n"
            f"🆔 Аккаунт: {user['account_id']}\n👤 Нікнейм: {user['nickname']}",
            reply_markup=profile_actions()
        )
        return

    context.user_data["profile_server"] = selected
    context.user_data["profile_mode"] = "account"
    await q.edit_message_text("🆔 Введіть номер вашого ігрового аккаунта.")

async def profile_text(update, context):
    mode = context.user_data.get("profile_mode")
    if not mode:
        return False
    text = (update.message.text or "").strip()
    if mode == "account":
        if not text.isdigit() or len(text) > 30:
            await update.message.reply_text("Номер аккаунта має містити лише цифри. Спробуйте ще раз.")
            return True
        context.user_data["profile_account"] = text
        context.user_data["profile_mode"] = "nickname"
        await update.message.reply_text("👤 Введіть ваш нікнейм у грі.")
        return True
    if mode == "nickname":
        if len(text) < 2 or len(text) > 80:
            await update.message.reply_text("Нікнейм має містити від 2 до 80 символів. Спробуйте ще раз.")
            return True
        context.user_data["profile_nickname"] = text
        context.user_data["profile_mode"] = "confirm"
        await update.message.reply_text(
            "━━━━━━━━━━━━━━\n🎮 ARVIS ONLINE\n━━━━━━━━━━━━━━\n\n"
            f"🌐 Сервер: {context.user_data['profile_server']}\n"
            f"🆔 Номер аккаунта: {context.user_data['profile_account']}\n"
            f"👤 Нікнейм: {context.user_data['profile_nickname']}\n\n"
            "Перевірте дані перед продовженням.",
            reply_markup=confirm_profile()
        )
        return True
    return False

async def confirm(update, context):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    update_profile(
        user_id,
        context.user_data.get("profile_server"),
        context.user_data.get("profile_account"),
        context.user_data.get("profile_nickname"),
    )
    for k in ("profile_mode","profile_server","profile_account","profile_nickname"):
        context.user_data.pop(k, None)
    await q.edit_message_text("✅ Дані профілю збережено.")
    await q.message.reply_text("Тепер можна створити звернення.", reply_markup=main_menu())

async def edit(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["profile_mode"] = "server"
    await q.edit_message_text("🌐 Виберіть сервер", reply_markup=servers())

async def profile_change(update, context):
    q = update.callback_query
    await q.answer()
    field = q.data.split(":")[-1]
    if field == "server":
        context.user_data["profile_mode"] = "change_server"
        await q.edit_message_text("🌐 Виберіть сервер", reply_markup=servers())
    elif field == "account":
        context.user_data["profile_mode"] = "change_account"
        await q.edit_message_text("🆔 Введіть новий номер аккаунта.")
    elif field == "nickname":
        context.user_data["profile_mode"] = "change_nickname"
        await q.edit_message_text("👤 Введіть новий нікнейм.")

async def profile_change_text(update, context):
    mode = context.user_data.get("profile_mode")
    if mode not in {"change_account","change_nickname"}:
        return False
    text = (update.message.text or "").strip()
    if mode == "change_account":
        if not text.isdigit():
            await update.message.reply_text("Номер аккаунта має містити лише цифри.")
            return True
        update_profile(update.effective_user.id, account_id=text)
    else:
        if not 2 <= len(text) <= 80:
            await update.message.reply_text("Нікнейм має містити від 2 до 80 символів.")
            return True
        update_profile(update.effective_user.id, nickname=text)
    context.user_data.pop("profile_mode", None)
    await update.message.reply_text("✅ Профіль оновлено.", reply_markup=main_menu())
    return True
