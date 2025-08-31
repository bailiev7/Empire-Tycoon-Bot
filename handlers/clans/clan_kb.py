from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message

from __init__ import *  # подключение к БД

clan_kb = Router()


class Clan_Kb(StatesGroup):
    quantity_money = State()


@clan_kb.callback_query(F.data.startswith("clan_list_"))
async def cmd_clan_list(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Проверяем клан
    cursor.execute("SELECT clan_id FROM game WHERE user_id = ?", (user_id,))
    clan_id = cursor.fetchone()[0]
    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    # Проверяем, разрешен ли просмотр списка
    cursor.execute("SELECT clan_list_status FROM clans WHERE clan_id = ?", (clan_id,))
    clan_list_status = cursor.fetchone()[0]
    if clan_list_status == "False":  # False или 0
        await callback.answer("❌ Список участников скрыт создателем клана!")
        return

    # Получаем участников
    cursor.execute("SELECT user_id, clan_status FROM game WHERE clan_id = ?", (clan_id,))
    members = cursor.fetchall()

    # Разделяем по статусам
    owner, senior_leaders, leaders, players = [], [], [], []

    for user_id, status in members:
        cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        name = result[0]

        if status == "создатель 👑":
            owner.append(f"👑 Создатель: <a href='tg://user?id={user_id}'>{name}</a>")
        elif status == "старший руководитель 🤴":
            senior_leaders.append(f"🤴 Старший руководитель: <a href='tg://user?id={user_id}'>{name}</a>")
        elif status == "руководитель ⭐⭐":
            leaders.append(f"⭐⭐ Руководитель: <a href='tg://user?id={user_id}'>{name}</a>")
        elif status == "участник ⭐":
            players.append(f"⭐ Участник: <a href='tg://user?id={user_id}'>{name}</a>")

    # Формируем текст
    text = f"📋 Список участников клана:\n━━━━━━━━━━━━━━━\n"

    if owner:
        text += "\n".join(owner) + "\n━━━━━━━━━━━━━━━\n"
    if senior_leaders:
        text += "\n".join(senior_leaders) + "\n━━━━━━━━━━━━━━━\n"
    if leaders:
        text += "\n".join(leaders) + "\n━━━━━━━━━━━━━━━\n"
    if players:
        text += "\n".join(players) + "\n━━━━━━━━━━━━━━━\n"

    text += f"Всего участников: {len(members):,}"

    await callback.message.answer(text)


@clan_kb.callback_query(F.data.startswith("clan_achievments_"))
async def cmd_clan_achievments(callback: CallbackQuery):
    cursor.execute("SELECT clan_id FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id = cursor.fetchone()[0]

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    cursor.execute("SELECT clan_achievments FROM clan_achievments WHERE clan_id = ?", (clan_id,))
    result = cursor.fetchall()

    if not result:
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ У клана пока что нет достижений"
        )
        return

    cursor.execute("SELECT clan_name FROM clans WHERE clan_id = ?", (clan_id,))
    clan_name = cursor.fetchone()[0]

    text_message = [f"🏅 Достижения клана <b>{clan_name}</b>:"]
    num = 0

    for clan_achievments, clan_achievments_date in result:
        num += 1
        text_message.append(f"🏆 {num}. <b>{clan_achievments}</b>")

    text_message = "\n".join(text_message)

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=text_message
    )


@clan_kb.callback_query(F.data.startswith("clan_safe_"))
async def cmd_clan_safe(callback: CallbackQuery):
    cursor.execute("SELECT clan_id FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id = cursor.fetchone()[0]

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    cursor.execute("SELECT clan_safe, clan_safe_status FROM clans WHERE clan_id = ?", (clan_id,))
    clan_safe, clan_safe_status = cursor.fetchone()

    text_message = [f"🏛 Вы в сейфе клана. Отсюда можно только пополнить сейф.\n"
                    f"⚠ Снимать деньги может только создатель!"]

    if clan_safe_status == "False":
        text_message.append("🚫 Баланс сейфа скрыт создателем.")

    else:
        text_message.append(f"💵 На баланс сейфа: {clan_safe:,}₽")

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💹 Пополнить",
                                     callback_data=f"go_clan_safe_{callback.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить",
                                     callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    text_message.append("\nℹ Для пополнения сейфа нажмите кнопку ниже, введите желаемую сумму, а затем подтвердите!")

    text_message = "\n".join(text_message)

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=text_message,
        reply_markup=inline_kb
    )


@clan_kb.callback_query(F.data.startswith("delete_message_"))
async def cmd_delete_message(callback: CallbackQuery, state: FSMContext):
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id
    )
    await state.clear()
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="❌ Отменено"
    )


@clan_kb.callback_query(F.data.startswith("go_clan_safe_"))
async def cmd_go_clan_safe(callback: CallbackQuery, state: FSMContext):
    cursor.execute("SELECT clan_id FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id = cursor.fetchone()[0]

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    await state.set_state(Clan_Kb.quantity_money)

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="ℹ Введите сумму, которую хотите положить в сейф клана.\n"
             "⚠ Снимать деньги с сейфа может только создатель!"
    )


@clan_kb.message(Clan_Kb.quantity_money)
async def cmd_clan_create(message: Message, state: FSMContext):
    quantity_money = message.text
    if not quantity_money.isdigit():
        await message.reply("❌ Мне нужно число, а не текст. Только число!")
        return

    cursor.execute("SELECT rubles FROM game WHERE user_id = ?", (message.from_user.id,))
    rubles = cursor.fetchone()[0]

    if rubles < int(quantity_money):
        await message.reply("❌ У вас нет столько денег!\n\n"
                            f"💰 Ваш баланс составляет {rubles:,}₽")
        return

    if int(quantity_money) < 10000:
        await message.reply("❌ Сумма недостаточная! Минимальное вложение 10,000₽")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Подтвердить",
                                     callback_data=f"confirm_clan_safe_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить",
                                     callback_data=f"delete_message_{message.from_user.id}")
            ]
        ]
    )

    await state.update_data(quantity_money=quantity_money)

    await state.set_state(None)

    await message.reply(f"⚠ Вы уверены что хотите положить {int(quantity_money):,}₽ в сейф безвозвратно?",
                        reply_markup=inline_kb)


@clan_kb.callback_query(F.data.startswith("confirm_clan_safe_"))
async def cmd_confirm_clan_safe(callback: CallbackQuery, state: FSMContext):
    cursor.execute("SELECT clan_id FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id = cursor.fetchone()[0]

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    cursor.execute("SELECT rubles, clan_id FROM game WHERE user_id = ?", (callback.from_user.id,))
    rubles, clan_id = cursor.fetchone()

    data = await state.get_data()
    quantity_money = int(data.get("quantity_money"))

    if rubles < quantity_money:
        await bot.send_message("❌ На вашем балансе недостаточно средств. Операция была отменена")
        await state.clear()
        return

    cursor.execute("SELECT clan_safe FROM clans WHERE clan_id = ?", (clan_id,))
    clan_safe = cursor.fetchone()[0]

    cursor.execute("UPDATE game SET rubles = ? WHERE user_id = ?", (rubles - quantity_money, callback.from_user.id,))
    conn.commit()

    cursor.execute("UPDATE clans SET clan_safe = ? WHERE clan_id = ?", (clan_safe + quantity_money, clan_id,))
    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"✔ Вы успешно вложили {quantity_money:,} в сейф клана!\n"
             f"💰 На балансе: {rubles - quantity_money:,}₽"
    )


@clan_kb.callback_query(F.data.startswith("clan_union_"))
async def cmd_clan_union(callback: CallbackQuery):
    await callback.answer(show_alert=True, text="⌛ Скоро..")


@clan_kb.callback_query(F.data.startswith("clan_add_friend_"))
async def cmd_clan_add_friend(callback: CallbackQuery):
    cursor.execute("SELECT clan_id FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id = cursor.fetchone()[0]

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    cursor.execute("SELECT clan_id FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id = cursor.fetchone()[0]

    cursor.execute("SELECT clan_name, clan_invite_status FROM clans WHERE clan_id = ?", (clan_id,))
    clan_name, clan_invite_status = cursor.fetchone()

    if clan_invite_status == "False":
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ Приглашения в клан было закрыто создателем клана!"
        )
        return

    invite_link = f"https://t.me/Test_TTF_bot?start=clan_{clan_id}_from_{callback.from_user.id}"

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"🔗 Ссылка для приглашения друга в клан <a href='{invite_link}'>{clan_name}</a>!"
    )


@clan_kb.callback_query(F.data.startswith("clan_leave_"))
async def cmd_clan_leave(callback: CallbackQuery):
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    if clan_status == "создатель 👑":
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="❌ Вы являетесь создателем и не можете покинуть клан!"
        )
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Покинуть клан",
                                     callback_data=f"confirm_clan_leave_{callback.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить",
                                     callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="⚠ Вы уверены что хотите покинуть клан?\n"
             "Ваши заслуги и статус будут утеряны!",
        reply_markup=inline_kb
    )


@clan_kb.callback_query(F.data.startswith("confirm_clan_leave_"))
async def cmd_confirm_clan_leave(callback: CallbackQuery):
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (callback.from_user.id,))
    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await callback.answer("❌ Вы не состоите ни в каком клане!")
        return

    cursor.execute("SELECT clan_name FROM clans WHERE clan_id = ?", (clan_id,))
    clan_name = cursor.fetchone()[0]

    cursor.execute("UPDATE game SET clan_id = '0', clan_status = 'False' WHERE user_id = ?", (callback.from_user.id,))
    conn.commit()

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"✔ Вы успешно покинули клан «<b><u>{clan_name}</u></b>»"
    )


@clan_kb.callback_query(F.data.startswith("clan_settings_"))
async def cmd_clan_settings(callback: CallbackQuery):
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
                                     callback_data=f"go_clan_avatar_{callback.from_user.id}"),
            ],
            [
                InlineKeyboardButton(text="🌟 Управлять должностями",
                                     callback_data=f"go_clan_admin_{callback.from_user.id}"),
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

    await bot.send_message(
        chat_id=callback.message.chat.id,
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
