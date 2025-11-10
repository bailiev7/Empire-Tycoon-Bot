from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime
import pytz

from __init__ import *

farm = Router()


@farm.message(F.text.casefold() == "фарм")
async def cmd_farm(message: Message):
    # Получаем текущее время по Москве
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.now(tz)
    current_hour = now.hour

    # Проверка: разрешено фармить только с 22:00 до 10:00

    cursor.execute("SELECT rubles FROM game WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    rubles = result[0]
    if message.chat.id == -1002914891844:
        if not (current_hour >= 23 or current_hour < 10):
            await message.reply("⏰ Фарм в этом чате доступен только с 23:00 до 10:00 по МСК!")
            return

        cursor.execute("UPDATE game SET rubles = ? WHERE user_id = ?", (rubles + 10, message.from_user.id,))
        conn.commit()
        await message.reply(
            f"Вы успешно нафармили 10 рублей!\n\nПока вы фармите в этой группе, вы получаете вдвое больше!!"
        )
    else:
        cursor.execute("SELECT premium_status FROM game WHERE user_id = ?", (message.from_user.id,))
        premium_status = cursor.fetchone()[0]

        if premium_status == "True":
            cursor.execute("UPDATE game SET rubles = ? WHERE user_id = ?", (rubles + 10, message.from_user.id,))
            conn.commit()
            await message.reply(
                f"Вы успешно нафармили 10 рублей благодаря <b><u>PREMIUM</u></b> статусу!"
            )
            return

        cursor.execute("UPDATE game SET rubles = ? WHERE user_id = ?", (rubles + 5, message.from_user.id,))
        conn.commit()

        cursor.execute("SELECT tutorial FROM game WHERE user_id = ?", (message.from_user.id,))
        tutorial = cursor.fetchone()[0]

        if tutorial == 2:
            cursor.execute("UPDATE game SET tutorial = '3' WHERE user_id = ?", (message.from_user.id,))
            conn.commit()

            await message.reply(
                f"Вы успешно нафармили 5 рублей!\n\nЧтобы получить фарм х2 вам необходим <b><u>PREMIUM</u></b> статус или вступить в нашу беседу!\n\n"
                f"Теперь перейдите в профиль. Введите команду <b><u>/profile</u></b>"
            )
            return

        await message.reply(
            f"Вы успешно нафармили 5 рублей!\n\nЧтобы получить фарм х2 вам необходим <b><u>PREMIUM</u></b> статус или вступить в нашу беседу!"
        )
