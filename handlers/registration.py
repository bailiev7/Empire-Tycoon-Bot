from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from __init__ import cursor, conn
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
import re

registration = Router()  # [1]


def db_table_user(user_id, name_profile, name_bot, age):
    cursor.execute("INSERT INTO user (user_id, name_profile, name_bot, age) VALUES (?, ?, ?, ?)",
                   (user_id, name_profile, name_bot, age))
    conn.commit()

    cursor.execute("INSERT INTO game (user_id) VALUES (?)", (user_id,))
    conn.commit()


class Registration(StatesGroup):
    name = State()
    age = State()


@registration.message(Command(commands=("рег", "регистрация", "registration", "reg")))  # [2]
async def cmd_registration(message: Message, state: FSMContext):
    cursor.execute("Select * FROM user WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    if result is None:
        await message.reply("Игрок, введи своё имя! Допустимы только русские или английские буквы.")
        await state.set_state(Registration.name)

    else:
        await message.reply("Игрок, ты уже зарегистрирован в нашей игре!")


@registration.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    user_name = message.text.strip()

    # Разрешаем буквы (рус/англ), пробелы, точки, подчеркивания и дефисы
    if not re.fullmatch(r"[a-zA-Zа-яА-ЯёЁ ._-]{5,20}", user_name):
        await message.reply(
            "Имя может содержать только русские или английские буквы, а также пробелы, точки, дефисы и подчёркивания.\n"
            "Допустимая длина — от 5 до 20 символов."
        )
        return

    # Сохраняем имя во временное состояние
    await state.update_data(name=user_name)

    # Клавиатура подтверждения
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
                InlineKeyboardButton(text="🔄 Изменить", callback_data="change")
            ]
        ]
    )

    await message.reply(
        f"Вы уверены, что хотите сохранить имя {user_name}?",
        reply_markup=inline_kb
    )


@registration.callback_query(F.data == "change")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Игрок, введи своё имя! Допустимы только русские или английские буквы.")
    await state.set_state(Registration.name)


@registration.callback_query(F.data == "confirm")
async def handle_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    await callback.message.edit_text(
        f"Отлично, имя {name} сохранено!\nИдем дальше. Укажи свой возраст! (подсказка: играть можно от 16 лет)")
    await state.set_state(Registration.age)


@registration.message(Registration.age)
async def process_name(message: Message, state: FSMContext):
    user_age = message.text
    if not user_age.isdigit():
        await message.reply("Мне нужен только возраст без текста (например: 18)")
        return

    if int(user_age) < 16:
        await message.reply(
            "Наш бот доступен пользователям от 16 лет. Попробуй снова через пару лет или введи его сейчас")
        return

    elif 50 < int(user_age) < 100:
        await message.reply("Кажется вы слишком старый для этой игры. Попробуйте снова")
        return

    elif int(user_age) >= 100:
        await message.reply("Вы прожили слишком много, введите корректный возраст!")
        return

    await state.update_data(age=message.text)
    data = await state.get_data()
    name = data.get("name")
    await state.clear()
    await message.reply(f"Отлично, возраст {user_age} сохранен")

    db_table_user(message.from_user.id, message.from_user.first_name, name, user_age)
