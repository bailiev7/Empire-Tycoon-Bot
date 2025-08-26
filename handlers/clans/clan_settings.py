from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message

from __init__ import *  # подключение к БД

clan_settings = Router()


class Clan_settings(StatesGroup):
    new_name = State()
    clan_kick = State()
    delete_clan = State()


@clan_settings.callback_query(F.data.startswith("change_clan_"))
async def cmd_go_clan_safe(callback: CallbackQuery):
    action = callback.data.split("_")
    action = "_".join(action[1:4])
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        return

    cursor.execute(f"SELECT {action} FROM clans WHERE clan_id = ?", (clan_id,))
    status = cursor.fetchone()[0]

    if status == "True":
        status_new = "False"

    else:
        status_new = "True"

    cursor.execute(f"UPDATE clans SET {action} = ? WHERE clan_id = ?", (status_new, clan_id,))
    conn.commit()

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏛 Отображение сейфа",
                                     callback_data=f"change_clan_safe_status_{callback.from_user.id}"),
                InlineKeyboardButton(text="➕ Отображение участников",
                                     callback_data=f"change_clan_list_status_{callback.from_user.id}"),
                InlineKeyboardButton(text="👥 Открытость клана",
                                     callback_data=f"change_clan_invite_status_{callback.from_user.id}")
            ],
            [
                InlineKeyboardButton(text="📜 Название клана",
                                     callback_data=f"go_clan_rename_{callback.from_user.id}"),
                InlineKeyboardButton(text="✒ Изменить описание",
                                     callback_data=f"go_clan_desc_{callback.from_user.id}"),
                InlineKeyboardButton(text="🖼 Изменить аватарку",
                                     callback_data=f"go_clan_avatar_{callback.from_user.id}")
            ],
            [
                InlineKeyboardButton(text="🚫 Изгнать участника",
                                     callback_data=f"go_clan_kick_{callback.from_user.id}"),
                InlineKeyboardButton(text="❌ Удалить клан",
                                     callback_data=f"go_clan_delete_{callback.from_user.id}"),
            ]
        ]
    )

    cursor.execute("SELECT clan_safe_status, clan_list_status, clan_invite_status FROM clans WHERE clan_id = ?",
                   (clan_id,))
    clan_safe_status, clan_list_status, clan_invite_status = cursor.fetchone()

    if clan_safe_status == "True":
        safe_emoji = "✔"
    else:
        safe_emoji = "❌"

    if clan_list_status == "True":
        list_emoji = "✔"
    else:
        list_emoji = "❌"

    if clan_invite_status == "True":
        invite_emoji = "✔"
    else:
        invite_emoji = "❌"

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=inline_kb,
        text=
        "⚙ <b>Управление кланом</b>\n\n"
        f"🏛 Видимость сейфа - {safe_emoji}\n"
        f"➕ Видимость участников - {list_emoji}\n"
        f"👥 Открытость клана - {invite_emoji}\n\n"
        f"📜 Переименовать клан\n"
        f"✒ Обновить описание\n"
        f"🖼 Поменять аватарку\n\n"
        "🚫 Изгнать участника\n"
        "❌ Удалить клан\n\n"
        "Будь внимателен — некоторые действия необратимы! ⚠"
    )


@clan_settings.callback_query(F.data.startswith("go_clan_rename_"))
async def cmd_go_clan_rename(callback: CallbackQuery, state: FSMContext):
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        return

    cursor.execute("SELECT bitcoins FROM game WHERE user_id = ?", (callback.from_user.id,))
    bitcoins = cursor.fetchone()[0]

    if bitcoins < 3:
        await callback.answer("❌ У вас недостаточно BTC для изменения названия!")
        return

    await state.set_state(Clan_settings.new_name)

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить",
                                     callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="Введите название на которое хотели бы поменять текущее!",
        reply_markup=inline_kb,
    )


@clan_settings.message(Clan_settings.new_name)
async def cmd_new_name(message: CallbackQuery, state: FSMContext):
    new_name = message.text

    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (message.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await message.reply("❌ Вы не состоите ни в каком клане!")
        return

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=message.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        return

    cursor.execute("SELECT bitcoins FROM game WHERE user_id = ?", (message.from_user.id,))
    bitcoins = cursor.fetchone()[0]

    if bitcoins < 3:
        await message.reply("❌ У вас недостаточно BTC для изменения названия!")
        return

    if not (5 <= len(new_name) <= 30):
        await message.reply(
            f"❌ Название клана должно быть длиной от 5 до 30 символов ({len(new_name)})"
        )
        return

    cursor.execute("SELECT clan_name FROM clans WHERE clan_id = ?", (clan_id,))
    clan_old_name = cursor.fetchone()[0]

    if clan_old_name == new_name:
        await message.reply("❌ Вы ввели то-же самое название!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Подтвердить",
                                     callback_data=f"confirm_clan_rename_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить создание",
                                     callback_data=f"delete_message_{message.from_user.id}")
            ]
        ]
    )

    await state.update_data(new_name=new_name)

    await message.reply(f"⚠ Вы уверены что хотите поменять название клана?\n"
                        f"«<b><u>{clan_old_name}</u></b>» → «<b><u>{new_name}</u></b>",
                        reply_markup=inline_kb)


@clan_settings.callback_query(F.data.startswith("confirm_clan_rename_"))
async def cmd_confirm_clan_rename(callback: CallbackQuery, state: FSMContext):
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        return

    cursor.execute("SELECY bitcoins FROM game WHERE user+id = ?", (callback.from_user.id,))
    bitcoins = cursor.fetchone()[0]

    if bitcoins < 3:
        await callback.answer("❌ У вас недостаточно BTC для изменения названия!")
        return

    data = await state.get_data()
    new_name = data.get("new_name")

    cursor.execute("UPDATE clans SET clan_name = ? WHERE clan_id = ?", (new_name, clan_id,))
    conn.commit()

    cursor.execute("UPDATE game SET bitcoins = ? WHERE user_id = ?", (bitcoins-3, callback.from_user.id,))
    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"Вы успешно сменили название клана на «<b><u>{new_name}</u></b>»"
    )

    await state.clear()


@clan_settings.callback_query(F.data.startswith("go_clan_desc_"))
async def cmd_go_clan_desc(callback: CallbackQuery):
    await callback.answer(show_alert=True, text="⌛ Скоро..")


@clan_settings.callback_query(F.data.startswith("go_clan_avatar_"))
async def cmd_go_clan_avatar(callback: CallbackQuery):
    await callback.answer(show_alert=True, text="⌛ Скоро..")


@clan_settings.callback_query(F.data.startswith("go_clan_kick_"))
async def cmd_go_clan_kick(callback: CallbackQuery, state: FSMContext):
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        return

    cursor.execute("SELECT user_id, clan_status FROM game WHERE clan_id = ? AND clan_status = 'участник ⭐'", (clan_id,))
    members = cursor.fetchall()

    # Разделяем по статусам
    players = []

    num = 0

    for user_id, status in members:
        num += 1
        cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        name = result[0]
        players.append(f"⭐ <u><b>{num}</b></u>. <a href='tg://user?id={user_id}'>{name}</a>")

    # Формируем текст
    text = f"📋 Список участников клана:\n━━━━━━━━━━━━━━━\n"

    text += "\n".join(players) + "\n━━━━━━━━━━━━━━━\n"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить",
                                     callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    text += "Напишите номер пользователя из этого списка, которого вы хотите исключить"

    await state.set_state(Clan_settings.clan_kick)

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=text,
        reply_markup=inline_kb
    )


@clan_settings.message(Clan_settings.clan_kick)
async def cmd_clan_kick(message: Message, state: FSMContext):
    clan_kick = message.text

    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (message.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    cursor.execute("SELECT user_id FROM game WHERE clan_id = ? AND clan_status = 'участник ⭐'", (clan_id,))
    user_id = cursor.fetchall()

    clan_kick_id = user_id[int(clan_kick)-1][0]

    if clan_id == 0:
        await message.answer("❌ Вы не состоите ни в каком клане!")
        await state.clear()

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=message.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        await state.clear()
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить",
                                     callback_data=f"delete_message_{message.from_user.id}")
            ]
        ]
    )

    if not clan_kick.isdigit():
        await message.reply("❌ Мне нужен только номер пользователя!", reply_markup=inline_kb)
        return

    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (clan_kick_id,))
    clan_id_kicked, clan_status_kicked = cursor.fetchone()

    if clan_id != clan_id_kicked:
        await message.reply("❌ Пользователь не состоит в вашем клане", reply_markup=inline_kb)
        return

    if clan_status_kicked != "участник ⭐":
        await message.reply("❌ Пользователь имеет права и не может быть исключен!", reply_markup=inline_kb)
        return

    cursor.execute("UPDATE game SET clan_id = '0', clan_status = 'False' WHERE user_id = ?", (clan_kick_id,))
    conn.commit()

    await message.reply(f"✔ <a href='tg://user?id={clan_kick_id}'>Пользователь</a> был успешно исключен из клана!")
    await state.clear()

    cursor.execute("SELECT clan_name FROM clans WHERE clan_id = ?", (clan_id,))
    clan_name = cursor.fetchone()[0]

    cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (message.from_user.id,))
    name_bot = cursor.fetchone()[0]

    await bot.send_message(
        chat_id=clan_kick_id,
        text=f"🚫 Вы были исключены из клана «<b><u>{clan_name}</u></b>»\n"
             f"🧑‍💻 Автор исключения: <a href='tg://user?id={message.from_user.id}'>{name_bot}</a>"
    )


@clan_settings.callback_query(F.data.startswith("go_clan_delete_"))
async def cmd_go_clan_delete(callback: CallbackQuery, state: FSMContext):
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        return

    await state.set_state(Clan_settings.delete_clan)

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="⚠ Вы уверены что хотите удалить клан безвозвратно?\n"
             "Если уверены в своём решении, напишите в ответ «Подтверждаю»"
    )


@clan_settings.message(Clan_settings.delete_clan)
async def cmd_clan_kick(message: Message, state: FSMContext):
    delete_clan_confirm = message.text

    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (message.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await message.answer("❌ Вы не состоите ни в каком клане!")
        await state.clear()

    if clan_status != "создатель 👑":
        await bot.send_message(
            chat_id=message.message.chat.id,
            text="❌ Настройки клана доступны только создателю клана!"
        )
        await state.clear()
        return

    if delete_clan_confirm != "Подтверждаю":
        await message.reply("❌ Подтверждение не выполнено. Операция отменена")
        await state.clear()
        return

    cursor.execute("SELECT user_id FROM game WHERE clan_id = ?", (clan_id,))
    list_user_id = cursor.fetchall()

    cursor.execute("SELECT clan_name FROM clans WHERE clan_id = ?", (clan_id,))
    clan_name = cursor.fetchone()[0]

    cursor.execute("DELETE FROM clans WHERE clan_id = ? AND owner_id = ?", (clan_id, message.from_user.id,))
    conn.commit()

    for user_id in list_user_id:
        if user_id[0] != message.from_user.id:
            cursor.execute("UPDATE game SET clan_id = '0', clan_status = 'False' WHERE user_id = ?", (user_id[0],))
            conn.commit()
            await bot.send_message(
                chat_id=user_id[0],
                text=f"❌ Клан «<b><u>{clan_name}</u></b>» был удалён его владельцем.\n"
                     "ℹ Вы можете вступить в другой клан!"
            )

    cursor.execute("UPDATE game SET clan_id = '0', clan_status = 'False' WHERE user_id = ?", (message.from_user.id,))
    conn.commit()

    await message.reply("✔ Удаление клана завершено. Его больше не существует")
