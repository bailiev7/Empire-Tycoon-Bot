import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from __init__ import *  # подключение к БД

quests = Router()


@quests.message(F.text.casefold() == "квесты")
@quests.message(Command(commands="quests"))
async def cmd_quests(message: Message):
    cursor.execute("SELECT qest_name, quest_desc FROM quests")
