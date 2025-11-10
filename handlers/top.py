import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

top = Router()


@top.message(F.text.casefold() == "топ")
@top.message(Command(commands="top"))
async def cmd_top(message: Message):

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="₽", callback_data=f"top_rubles_{message.from_user.id}"),
                InlineKeyboardButton(text="$", callback_data=f"top_dollars_{message.from_user.id}"),
                InlineKeyboardButton(text="₿", callback_data=f"top_bitcoins_{message.from_user.id}")
            ]
        ]
    )

    cursor.execute("SELECT tutorial FROM game WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    tutorial = result[0]

    if tutorial == 7:
        cursor.execute("UPDATE game SET tutorial = '8' WHERE user_id = ?", (message.from_user.id,))
        conn.commit()

        await message.reply("🏅 Здесь ты можешь посмотреть статистику игроков в боте по разным валютам, а также узнать своё место. Выбери валюту ниже", reply_markup=inline_kb)
        return

    await message.reply("🏅 Выберите статистику ниже", reply_markup=inline_kb)


@top.callback_query(F.data.startswith("top_"))
async def cmd_top(callback: CallbackQuery):
    raw = callback.data.split("_")

    type_top = raw[1]

    cursor.execute(f"SELECT user_id, {type_top}, premium_status FROM game ORDER BY {type_top} DESC")
    result = cursor.fetchall()

    if type_top == "rubles":
        type_top = "₽"
        text_type_top = "рублям"

    elif type_top == "dollars":
        type_top = "$"
        text_type_top = "долларам"

    elif type_top == "bitcoins":
        type_top = "₿"
        text_type_top = "биткоинам"

    text_message = [f"🏅 Статистика по {text_type_top} собрана:"]

    num = 0

    user_top = []

    for user_id, count, premium_status in result:
        num += 1
        if user_id == callback.from_user.id:
            user_top = num

        if num <= 10 and count > 0:
            cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (user_id,))
            name_bot = cursor.fetchone()[0]

            if premium_status == "True":
                text_message.append(f"{num}. <b><u>[PREMIUM]</u></b> <a href='tg://user?id={user_id}'>{name_bot}</a> - {int(count):,}{type_top}")

            else:
                text_message.append(f"{num}. <a href='tg://user?id={user_id}'>{name_bot}</a> - {int(count):,}{type_top}")

    text_message.append(f"\n👤 Вы находитесь на {user_top} месте!")

    text_message = "\n".join(text_message)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text_message
    )
