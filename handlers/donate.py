import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message

from __init__ import *  # подключение к БД

donate = Router()


@donate.message(F.text.casefold() == "донат")
@donate.message(Command(commands="donate"))
async def cmd_donate(message: Message):
    await message.reply(
        "💲 Для покупки валюты ознакомьтесь с курсом и акциями\n"
        "Игровая валюта | Реальная валюта\n"
        "10,000,000₽ – 1.99$\n"
        "50,000,000₽ – 7.99$\n"  # чуть дешевле за пакет
        "100,000,000₽ – 14.99$\n\n"  # ещё дешевле за пакет
        "5₿ – 7.99$\n"
        "10₿ – 14.99$\n"  # скидка на 10 BTC
        "20₿ – 24.99$\n\n"
        "💰 За приобретением можете обратиться к <a href='t.me/bailiev'>владельцу</a>!"  # скидка на 20 BTC
    )
