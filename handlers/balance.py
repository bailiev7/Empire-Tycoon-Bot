import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

balance = Router()


@balance.message(F.text.casefold().in_(["б", "баланс"]))
@balance.message(Command(commands="balance"))
async def cmd_balance(message: Message):
    cursor.execute("SELECT rubles, dollars, bitcoins FROM game WHERE user_id = ?", (message.from_user.id,))
    rubles, dollars, bitcoins = cursor.fetchone()

    await message.reply(f"💳 Баланс рублей: <u>{rubles:,}</u>₽\n"
                        f"💵 Баланс долларов: <u>{dollars:,}</u>$\n"
                        f"💹 Баланс биткоинов: <u>{round(bitcoins, 1):,}</u>₿\n")
