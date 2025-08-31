import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

casino = Router()


@casino.message(F.text.casefold() == "казино")
async def cmd_casino(message: Message):

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="♠ Poker", callback_data=f"start_poker_{message.from_user.id}"),
                InlineKeyboardButton(text="♣ BlackJack", callback_data=f"go_blackjack_{message.from_user.id}")
            ]
        ]
    )

    await message.reply("🃏 Выберите желаемую игру ниже", reply_markup=inline_kb)
