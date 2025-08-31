import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

referal = Router()


@referal.callback_query(F.data.startswith("referal_link_"))
async def cmd_referal_link(callback: CallbackQuery):
    cursor.execute("SELECT referal_count, referal_level FROM game WHERE user_id = ?", (callback.from_user.id,))
    referal_count, referal_level = cursor.fetchone()

    invite_link = f"https://t.me/Test_TTF_bot?start=invite_{callback.from_user.id}"

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"Ваш реферальный профиль:\n"
             f"🌟 Уровень: {referal_level}\n"
             f"👥 Пригласили: {referal_count} игроков\n"
             f"💰 Для повышения уровня пригласите ещё {referal_level*10} игроков\n"
             f"━━━━━━━━━━━━━━━\n"
             f"🔗 Реферальная ссылка:\n"
             f"<a href='{invite_link}'>Начни играть!</a>"
    )
