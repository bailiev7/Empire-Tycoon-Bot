import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

shop = Router()


@shop.message(F.text.casefold() == "магазин")
async def cmd_top(message: Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚗 Автомобили", callback_data=f"shop_cars_{message.from_user.id}"),
                InlineKeyboardButton(text="🏢 Бизнесы", callback_data=f"shop_business_{message.from_user.id}"),
                InlineKeyboardButton(text="🚢 Яхты", callback_data=f"shop_yacht_{message.from_user.id}")
            ]
        ]
    )

    await message.reply("🛍 Выберите нужный магазин", reply_markup=inline_kb)
