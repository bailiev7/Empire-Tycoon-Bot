import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message

from __init__ import *  # подключение к БД

help = Router()


@help.message(F.text.casefold() == "помощь")
@help.message(Command(commands="help"))
async def cmd_help(message: Message):
    await message.reply("📜 Список команд вы сможете найти тут: <a href='t.me/Empire_Tycoon_Help'>Empire Tycoon Help</a>")
