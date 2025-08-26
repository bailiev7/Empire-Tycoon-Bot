from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message

from __init__ import *  # подключение к БД

clan_create = Router()


class CreateClan(StatesGroup):
    clan_name = State()


def db_table_clan(owner_id, clan_name):
    cursor.execute(
        "INSERT INTO clans (owner_id, clan_name) "
        "VALUES (?, ?)",
        (owner_id, clan_name)
    )
    conn.commit()


@clan_create.message(F.text.casefold() == "создать клан")
@clan_create.message(Command(commands="create_clan"))
async def cmd_clan_create(message: Message, state: FSMContext):
    cursor.execute("SELECT clan_name FROM clans WHERE owner_id = ?",  (message.from_user.id,))
    result = cursor.fetchone()

    if result:
        business_name = result[0]
        await message.reply(f"❌ У вас уже есть свой клан b><u>{business_name}</u></b>!")
        return

    cursor.execute("SELECT bitcoins FROM game WHERE user_id = ?", (message.from_user.id,))
    bitcoins = cursor.fetchone()[0]

    if bitcoins < 10:
        await message.reply(f"❌ У вас недостаточно BTC ({round(bitcoins, 1):,}/10)")
        return

    else:
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Отменить создание",
                                         callback_data=f"cansel_{message.from_user.id}")
                ]
            ]
        )

        await state.set_state(CreateClan.clan_name)
        await message.reply(
            "📜 Для создания клана введите желаемое название в следующем сообщении!",
            reply_markup=inline_kb
        )


@clan_create.message(CreateClan.clan_name)
async def cmd_clan_create(message: Message, state: FSMContext):
    clan_name = message.text.strip()

    # Разрешаем буквы (рус/англ), пробелы, точки, подчеркивания и дефисы
    if not (5 <= len(clan_name) <= 30):
        await message.reply(
            f"❌ Название клана должно быть длиной от 5 до 30 символов ({len(clan_name)})"
        )
        return

    await state.update_data(clan_name=clan_name)

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Подтвердить",
                                     callback_data=f"confirm_clan_name_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить создание",
                                     callback_data=f"cansel_{message.from_user.id}")
            ]
        ]
    )

    await message.reply(
        f"❌ Вы уверены что хотите сохранить название «<b><u>{clan_name}</u></b>»?\n"
        f"ℹ Для повтора напишите желаемое название снова\n"
        f"⚠ Изменение названия клана после создания будет платным!",
        reply_markup=inline_kb
    )


@clan_create.callback_query(F.data.startswith('confirm_clan_name_'))
async def cmd_clan_create(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    clan_name = data.get("clan_name")

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Создать клан",
                                     callback_data=f"create_clan_{callback.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить создание",
                                     callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"Название «<b><u>{clan_name}</u></b>» сохранено\n"
             f"Подтвердите создание клана.\n"
             f"С вашего баланса будет списано 10 BTC!",
        reply_markup=inline_kb
    )


@clan_create.callback_query(F.data.startswith('create_clan_'))
async def cmd_clan_create(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    clan_name = data.get("clan_name")

    cursor.execute("SELECT bitcoins FROM game WHERE user_id = ?", (callback.from_user.id,))
    bitcoins = cursor.fetchone()[0]

    if bitcoins < 10:
        await callback.answer(f"❌ У вас недостаточно BTC! ({round(bitcoins)}/10)")
        return

    cursor.execute("UPDATE game SET bitcoins = ? WHERE user_id = ?", (bitcoins-10, callback.from_user.id,))
    conn.commit()

    db_table_clan(callback.from_user.id, clan_name)

    cursor.execute("SELECT clan_id FROM clans WHERE owner_id = ?", (callback.from_user.id,))
    clan_id = cursor.fetchone()[0]

    cursor.execute("UPDATE game SET clan_id = ? WHERE user_id = ?", (clan_id, callback.from_user.id,))
    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"🎉Вы успешно создали клан «<b><u>{clan_name}</u></b>».\n"
             f"✔ Его айди: <u>{clan_id}</u>\n"
             f"ℹ Для просмотра клана напишите <b><u>/my_clan</u></b>"
    )
    await state.clear()
