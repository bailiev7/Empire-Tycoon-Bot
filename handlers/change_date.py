import time
import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

change_date = Router()


class Change_Date(StatesGroup):
    name = State()


@change_date.callback_query(F.data.startswith("change_date_"))
async def cmd_change_date(callback: CallbackQuery):

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Изменить имя", callback_data=f"change_name_{callback.from_user.id}")
            ]
        ]
    )

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="✒ Выберите что хотите изменить", reply_markup=inline_kb)


@change_date.callback_query(F.data.startswith("change_name_"))
async def cmd_change_name(callback: CallbackQuery, state: FSMContext):
    cursor.execute(
        "SELECT value FROM inventory WHERE user_id = ? AND item_type = 'nick'", (callback.from_user.id,))
    result = cursor.fetchone()

    nick = None

    if result:
        nick = result[0]

    cursor.execute("SELECT bitcoins FROM game WHERE user_id = ?",
                   (callback.from_user.id,))
    bitcoins = cursor.fetchone()[0]

    if nick == 0:
        if bitcoins < 5:
            await bot.send_message(f"❌ У вас недостаточно BTC ({bitcoins}/5)")
            return

        text_message = "⚠ Изменение имени стоит 5₿. Введите желаемый ник, а затем подтвердите изменение!"

    else:
        text_message = "⚠ Изменение имени стоит 5₿, но у вас есть токен смены имени. Он потратится вместо BTC!.\nВведите желаемый ник, а затем подтвердите изменение!"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await state.set_state(Change_Date.name)
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text_message,
        reply_markup=inline_kb
    )


@change_date.message(Change_Date.name)
async def process_name(message: Message, state: FSMContext):
    user_name = message.text.strip()

    # Разрешаем буквы (рус/англ), пробелы, точки, подчеркивания и дефисы
    if not re.fullmatch(r"[a-zA-Zа-яА-ЯёЁ ._-]{5,20}", user_name):
        await message.reply(
            "❌ Имя может содержать только русские или английские буквы, а также пробелы, точки, дефисы и подчёркивания.\n"
            "Допустимая длина — от 5 до 20 символов."
        )
        return

    # Сохраняем имя во временное состояние
    await state.update_data(name=user_name)

    # Клавиатура подтверждения
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить", callback_data=f"confirm_rename_{message.from_user.id}"),
                InlineKeyboardButton(
                    text="🔄 Изменить", callback_data=f"change_name_{message.from_user.id}")
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{message.from_user.id}")
            ]
        ]
    )

    await message.reply(
        f"Вы уверены, что хотите изменить имя на {user_name}?",
        reply_markup=inline_kb
    )


@change_date.callback_query(F.data.startswith("confirm_rename_"))
async def handle_confirm(callback: CallbackQuery, state: FSMContext):
    nick = None
    data = await state.get_data()
    name = data.get("name")

    cursor.execute(
        "SELECT value FROM inventory WHERE user_id = ? AND item_type = 'nick'", (callback.from_user.id,))
    nick = cursor.fetchone()[0]

    cursor.execute("SELECT bitcoins FROM game WHERE user_id = ?",
                   (callback.from_user.id,))
    bitcoins = cursor.fetchone()[0]

    if nick == 0:
        cursor.execute("UPDATE game SET bitcoins = ? WHERE user_id = ?",
                       (bitcoins-5, callback.from_user.id,))
        text_message = f"Отлично, имя изменено на {name}!\nС вашего баланса списано 5₿"

    else:
        if bitcoins < 5:
            await callback.answer("❌ У вас недостаточно BTC!")
            await state.clear()
            return

        cursor.execute("UPDATE inventory SET nick = ? WHERE user_id = ?",
                       (nick-1, callback.from_user.id,))
        text_message = f"Отлично, имя изменено на {name}!\nВы потратили 1 токен смены имени!"

    cursor.execute("UPDATE user SET name_bot = ? WHERE user_id = ?",
                   (name, callback.from_user.id,))
    conn.commit()

    await callback.message.edit_text(
        text=text_message
    )

    await state.clear()
