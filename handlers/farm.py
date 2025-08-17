from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from __init__ import *


farm = Router()  # [1]


@farm.message(F.text.casefold() == "фарм")  # [2]
async def cmd_farm(message: Message):
    cursor.execute("SELECT rubles FROM game WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    rubles = result[0]

    cursor.execute("UPDATE game SET rubles = ? WHERE user_id = ?", (rubles+5, message.from_user.id,))
    conn.commit()

    await message.reply(f"Вы успешно нафармили 5 рублей!\n\nДля фармы в х2 вступите в нашу группу и фармите там!")
