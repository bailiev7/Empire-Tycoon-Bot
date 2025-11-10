import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from __init__ import *  # подключение к БД

admin_panel = Router()


class AdminPanel(StatesGroup):
    user_id = State()
    type_money = State()
    quantity_money = State()
    quantity_money_take = State()


@admin_panel.message(F.text.casefold().startswith("/new_promo"))
async def cmd_new_promo(message: Message):
    if message.from_user.id not in [6358045048]:
        await message.reply("❌ Вы не являетесь админом!")
        return

    if message.text == "/new_promo":
        await message.reply("❌ Введите новое промо!")
        return

    try:
        promo_code = message.text.split()[1]
        promo_reward = int(message.text.split()[2])
        promo_reward_type = message.text.split()[3]
        promo_activate = int(message.text.split()[4])

    except:
        await message.reply("❌ Неправильно введена команда!")
        return

    if promo_reward_type == "rubles":
        reward_text = "₽"

    elif promo_reward_type == "dollars":
        reward_text = "$"

    elif promo_reward_type == "bitcoins":
        reward_text = "₿"

    else:
        await message.reply("❌ Неправильно введена команда!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Подтвердить",
                                     callback_data=f"new_promo_{promo_code}_{promo_reward}_{promo_reward_type}_{promo_activate}_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить",
                                     callback_data=f"delete_message_{message.from_user.id}")
            ]
        ]
    )

    await message.reply(
        text="⚠ Вы уверены что хотите создать промокод?\n"
             f"<b>📜 Кодовое название: {promo_code}\n"
             f"👥 Количество активаций: {promo_activate}\n"
             f"💰 Награда: {promo_reward:,}{reward_text}</b>",
        reply_markup=inline_kb
    )


@admin_panel.callback_query(F.data.startswith("new_promo_"))
async def cmd_new_promo(callback: CallbackQuery):
    action = callback.data.split("_")

    promo_code = action[2]
    promo_reward = int(action[3])
    promo_reward_type = action[4]
    promo_activate = int(action[5])

    cursor.execute(
        "INSERT INTO promo(promo_code, promo_reward, promo_reward_type, promo_activate) VALUES(?, ?, ?, ?)",
        (promo_code, promo_reward, promo_reward_type, promo_activate)
    )
    conn.commit()

    if promo_reward_type == "rubles":
        reward_text = "₽"

    elif promo_reward_type == "dollars":
        reward_text = "$"

    elif promo_reward_type == "bitcoins":
        reward_text = "₿"

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"📜 Промокод был успешно создан!\n\n"
        f"<b>📜 Кодовое название: {promo_code}\n"
        f"👥 Количество активаций: {promo_activate}\n"
        f"💰 Награда: {promo_reward:,}{reward_text}</b>"
    )


@admin_panel.message(F.text.casefold().startswith(".админ"))
async def cmd_admin_panel(message: Message):
    if message.from_user.id not in [6358045048]:
        await message.reply("❌ Вы не являетесь админом!")
        return

    if message.text == ".админ":
        await message.reply("❌ Введите айди игрока!")
        return

    user_id = message.text.split()[1]

    cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        await message.reply("❌ Такого игрока не найдено!")
        return

    name_bot = result[0]

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌟 Выдать PREMIUM",
                                     callback_data=f"go_give_premium_{user_id}_{message.from_user.id}"),
                InlineKeyboardButton(text="💰 Выдать деньги",
                                     callback_data=f"go_give_money_{user_id}_{message.from_user.id}")
            ],
            [
                InlineKeyboardButton(text="🌟 Забрать PREMIUM",
                                     callback_data=f"go_take_premium_{user_id}_{message.from_user.id}"),
                InlineKeyboardButton(text="💰 Забрать деньги",
                                     callback_data=f"go_take_money_{user_id}_{message.from_user.id}")
            ],
            [
                InlineKeyboardButton(text="🚫 Заблокировать игрока",
                                     callback_data=f"go_ban_user_{user_id}_{message.from_user.id}"),
                InlineKeyboardButton(text="✔ Разблокировать игрока",
                                     callback_data=f"go_unban_user_{user_id}_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Удалить игрока",
                                     callback_data=f"go_delete_user_{user_id}_{message.from_user.id}")
            ],
            [
                InlineKeyboardButton(text="📜 Информация о игроке",
                                     callback_data=f"go_info_user_{user_id}_{message.from_user.id}")
            ]
        ]
    )

    await message.reply(f"⚙ Выберете тип взаимодействия с игроком <a href='tg://user?id={user_id}'>{name_bot}</a>",
                        reply_markup=inline_kb)


@admin_panel.callback_query(F.data.startswith("go_give_premium_"))
async def cmd_go_give_premium(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = action[3]

    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1️⃣ день",
                                     callback_data=f"give_premium_1_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="3️⃣ дня", callback_data=f"give_premium_3_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(text="7️⃣ дней",
                                     callback_data=f"give_premium_7_{user_id}_{callback.from_user.id}"),
            ],
            [
                InlineKeyboardButton(text="1️⃣5️⃣ дней",
                                     callback_data=f"give_premium_15_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(text="3️⃣0️⃣ дней",
                                     callback_data=f"give_premium_30_{user_id}_{callback.from_user.id}")
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"Выберите срок выдачи <b><u>PREMIUM</u></b> статуса <a href='tg://user?id={user_id}'>игроку</a>",
        reply_markup=inline_kb
    )


@admin_panel.callback_query(F.data.startswith("give_premium_"))
async def cmd_give_premium(callback: CallbackQuery):
    action = callback.data.split("_")
    days = int(action[2])  # срок премиума
    user_id = int(action[3])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    # Проверяем, есть ли уже такой токен в инвентаре
    cursor.execute(
        "SELECT amount FROM inventory WHERE user_id=? AND item_type='vip' AND value=?",
        (user_id, f"{days}day")
    )
    row = cursor.fetchone()

    if row:
        # Если есть — увеличиваем количество
        cursor.execute(
            "UPDATE inventory SET amount = amount + 1 WHERE user_id=? AND item_type='vip' AND value=?",
            (user_id, f"{days}day")
        )
    else:
        # Если нет — создаём новый слот
        cursor.execute(
            "INSERT INTO inventory (user_id, item_type, value, amount) VALUES (?, 'vip', ?, 1)",
            (user_id, f"{days}day")
        )

    conn.commit()
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"✅ Пользователю выдан VIP на {days} день(ей) в инвентарь!"
    )
    await bot.send_message(
        chat_id=user_id,
        text=f"🌟 Вам был выдан <u><b>PREMIUM</b></u> статус на {days} дн.\n\n"
        f"✔ Активировать его можно через <b><u>/inventory</u></b>!"
    )


@admin_panel.callback_query(F.data.startswith("go_give_money_"))
async def cmd_go_give_money(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[3])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="₽", callback_data=f"give_money_rubles_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="$", callback_data=f"give_money_dollars_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="₿", callback_data=f"give_money_bitcoins_{user_id}_{callback.from_user.id}")
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"💰 Выберите сумму которую хотите выдать <a href='tg://user?id={user_id}'>игроку</a>",
        reply_markup=inline_kb
    )


@admin_panel.callback_query(F.data.startswith("give_money_"))
async def cmd_give_money(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")
    type_money = action[2]
    user_id = int(action[3])

    cursor.execute(
        f"SELECT {type_money} FROM game WHERE user_id = ?", (user_id,))
    type_money_count = cursor.fetchone()[0]

    if type_money == "rubles":
        type_money_text = "рублей"
        type_money_text_2 = "₽"

    elif type_money == "dollars":
        type_money_text = "долларов"
        type_money_text_2 = "$"

    elif type_money == "bitcoins":
        type_money_text = "биткоинов"
        type_money_text_2 = "₿"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"💰 Укажите выдаваемою сумму {type_money_text} <a href='tg://user?id={user_id}'>игроку</a>!\n\n"
        f"💳 Его баланс составляет: {type_money_count:,}{type_money_text_2}",
        reply_markup=inline_kb
    )

    await state.update_data(type_money=type_money, user_id=user_id)

    await state.set_state(AdminPanel.quantity_money)


@admin_panel.message(AdminPanel.quantity_money)
async def cmd_clan_create(message: Message, state: FSMContext):
    quantity_money = message.text
    if not quantity_money.isdigit():
        await message.reply("❌ Мне нужно число, а не текст. Только число!")
        return

    data = await state.get_data()
    user_id = int(data.get("user_id"))
    type_money = data.get("type_money")
    await state.clear()

    cursor.execute(
        f"SELECT {type_money} FROM game WHERE user_id = ?", (user_id,))
    type_money_count = cursor.fetchone()[0]

    cursor.execute(f"UPDATE game SET {type_money} = ? WHERE user_id = ?",
                   (type_money_count + int(quantity_money), user_id,))
    conn.commit()

    if type_money == "rubles":
        type_money_text = "₽"

    elif type_money == "dollars":
        type_money_text = "$"

    elif type_money == "bitcoins":
        type_money_text = "₿"

    await message.reply(
        text=f"✔ Вы успешно выдали <a href='tg://user?id={user_id}'>игроку</a> {int(quantity_money):,}{type_money_text}!"
    )

    await bot.send_message(
        chat_id=user_id,
        text=f"💰 Вам было выдано {int(quantity_money):,}{type_money_text}!\n\n"
        f"💳 Ваш баланс: {type_money_count + int(quantity_money):,}{type_money_text}"
    )


# ------------ #
@admin_panel.callback_query(F.data.startswith("go_take_premium_"))
async def cmd_go_take_premium(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = action[3]

    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    cursor.execute(
        "SELECT premium_status FROM game WHERE user_id = ?", (user_id,))
    premium_status = cursor.fetchone()[0]

    if premium_status == "False":
        await callback.answer("❌ У игрока нет PREMIUM статуса!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Подтвердить",
                                     callback_data=f"take_premium_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"⚠ Вы уверены что хотите забрать <u><b>PREMIUM</b></u> статус у <a href='tg://user?id={user_id}'>игрока</a>",
        reply_markup=inline_kb
    )


@admin_panel.callback_query(F.data.startswith("take_premium_"))
async def cmd_give_premium(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[2])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    cursor.execute(
        "UPDATE game SET premium_status = 'False', premium_until = '0' WHERE user_id = ?", (user_id,))
    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"✅ У пользователя был отобран <u><b>PREMIUM</b></u> статус!"
    )

    await bot.send_message(
        chat_id=user_id,
        text="У вас был отобран <u><b>PREMIUM</b></u> статус!"
    )


@admin_panel.callback_query(F.data.startswith("go_take_money_"))
async def cmd_go_give_money(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[3])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="₽", callback_data=f"take_money_rubles_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="$", callback_data=f"take_money_dollars_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="₿", callback_data=f"take_money_bitcoins_{user_id}_{callback.from_user.id}")
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"💰 Выберите сумму которую хотите снять с <a href='tg://user?id={user_id}'>игрока</a>",
        reply_markup=inline_kb
    )


@admin_panel.callback_query(F.data.startswith("take_money_"))
async def cmd_give_money(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")
    type_money = action[2]
    user_id = int(action[3])

    cursor.execute(
        f"SELECT {type_money} FROM game WHERE user_id = ?", (user_id,))
    type_money_count = cursor.fetchone()[0]

    if type_money == "rubles":
        type_money_text = "рублей"
        type_money_text_2 = "₽"

    elif type_money == "dollars":
        type_money_text = "долларов"
        type_money_text_2 = "$"

    elif type_money == "bitcoins":
        type_money_text = "биткоинов"
        type_money_text_2 = "₿"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"💰 Укажите отнимаемую сумму {type_money_text} <a href='tg://user?id={user_id}'>игроку</a>!\n\n"
        f"💳 Его баланс составляет: {type_money_count:,}{type_money_text_2}",
        reply_markup=inline_kb
    )

    await state.update_data(type_money=type_money, user_id=user_id)

    await state.set_state(AdminPanel.quantity_money_take)


@admin_panel.message(AdminPanel.quantity_money_take)
async def cmd_clan_create(message: Message, state: FSMContext):
    quantity_money_take = message.text
    if not quantity_money_take.isdigit():
        await message.reply("❌ Мне нужно число, а не текст. Только число!")
        return

    data = await state.get_data()
    user_id = int(data.get("user_id"))
    type_money = data.get("type_money")

    await state.clear()

    cursor.execute(
        f"SELECT {type_money} FROM game WHERE user_id = ?", (user_id,))
    type_money_count = cursor.fetchone()[0]

    cursor.execute(f"UPDATE game SET {type_money} = ? WHERE user_id = ?",
                   (type_money_count - int(quantity_money_take), user_id,))
    conn.commit()

    if type_money == "rubles":
        type_money_text = "₽"

    elif type_money == "dollars":
        type_money_text = "$"

    elif type_money == "bitcoins":
        type_money_text = "₿"

    await message.reply(
        text=f"✔ Вы успешно отняли с <a href='tg://user?id={user_id}'>игрока</a> {int(quantity_money_take):,}{type_money_text}!"
    )

    await bot.send_message(
        chat_id=user_id,
        text=f"💰 С вашего баланса было отнято {int(quantity_money_take):,}{type_money_text}!\n\n"
        f"💳 Ваш баланс: {type_money_count - int(quantity_money_take):,}{type_money_text}"
    )


@admin_panel.callback_query(F.data.startswith("go_ban_user_"))
async def cmd_go_ban_user(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[3])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    cursor.execute("SELECT ban FROM user WHERE user_id = ?", (user_id,))
    ban = cursor.fetchone()[0]

    if ban == "True":
        await callback.answer("❌ Игрок уже заблокирован!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Заблокировать",
                                     callback_data=f"ban_user_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (user_id,))
    name_bot = cursor.fetchone()[0]

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=inline_kb,
        text=f"⚠ Вы уверены что хотите заблокировать игрока <a href='tgg://user?id={user_id}'>{name_bot}</a>?"
    )


@admin_panel.callback_query(F.data.startswith("ban_user_"))
async def cmd_ban_user(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[2])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    cursor.execute("SELECT ban FROM user WHERE user_id = ?", (user_id,))
    ban = cursor.fetchone()[0]

    if ban == "True":
        await callback.answer("❌ Игрок уже заблокирован!!")
        return

    cursor.execute(
        "UPDATE user SET ban = 'True' WHERE user_id = ?", (user_id,))
    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"✔ <a href='tgg://user?id={user_id}'>Игрок</a> успешно заблокирован!"
    )

    await bot.send_message(
        chat_id=user_id,
        text="🚫 К сожалению вы были заблокированы в нашем боте за нарушение правил.\n\n"
             "Обжаловать блокировку можете обратившись к <a href='https://t.me/alievww'>владельцу</a> бота!"
    )


@admin_panel.callback_query(F.data.startswith("go_unban_user_"))
async def cmd_go_unban_user(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[3])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    cursor.execute("SELECT ban FROM user WHERE user_id = ?", (user_id,))
    ban = cursor.fetchone()[0]

    if ban == "False":
        await callback.answer("❌ Игрок не заблокирован!")
        return

    cursor.execute(
        "UPDATE user SET ban = 'False' WHERE user_id = ?", (user_id,))
    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="✔ <a href='tgg://user?id={user_id}'>Игрок</a> успешно разблокирован!"
    )

    await bot.send_message(
        chat_id=user_id,
        text="✔ Вы были разблокированы в нашем боте!\n"
             "🎉 Ваши дейсвтвия или поведение посчитали невиновными"
    )


@admin_panel.callback_query(F.data.startswith("go_delete_user_"))
async def cmd_go_delete_user(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[3])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✔ Удалить", callback_data=f"delete_user_{user_id}_{callback.from_user.id}"),
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")
            ]
        ]
    )

    cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (user_id,))
    name_bot = cursor.fetchone()[0]

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=inline_kb,
        text=f"⚠ Вы уверены что хотите удалить игрока <a href='tgg://user?id={user_id}'>{name_bot}</a> со всей базы данных безвозвратно?"
    )


@admin_panel.callback_query(F.data.startswith("delete_user_"))
async def cmd_delete_user(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[2])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    cursor.execute("DELETE FROM user WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM game WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM business WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))

    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="✔ Игрок был успешно удален со всей базы данных"
    )

    await bot.send_message(
        chat_id=user_id,
        text="❌ Ваш прогресс в боте был анулирован. Вы можете начать снова написав <u><b>/registration</b></u>!"
    )


@admin_panel.callback_query(F.data.startswith("go_info_user_"))
async def cmd_go_info_user(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = int(action[3])

    # Проверка на админа
    if callback.from_user.id not in [6358045048]:
        await callback.answer("❌ Вы не являетесь админом!")
        return

    cursor.execute(
        "SELECT name_profile, name_bot, age, ban FROM user WHERE user_id = ?", (user_id,))
    name_profile, name_bot, age, ban = cursor.fetchone()

    cursor.execute("SELECT rubles, dollars, bitcoins, profit_hour, premium_status, premium_until, clan_id, clan_status, referal_level, referal_all FROM game WHERE user_id = ?", (user_id,))
    rubles, dollars, bitcoins, profit_hour, premium_status, premium_until, clan_id, clan_status, referal_level, referal_all = cursor.fetchone()

    if ban == "True":
        ban_text = "залокирован 🚫"

    else:
        ban_text = "не заблокирован ✔"

    if premium_status == "True":
        now = int(time.time())
        remaining = premium_until - now

        days = remaining // 86400  # 1 день = 86400 секунд
        premium_status = (f"активен ✔\n"
                          f"⌛ Осталось {days} дн.")

    else:
        premium_status = "неактивен ❌"

    if clan_id != 0:
        cursor.execute(
            "SELECT clan_name FROM clans WHERE clan_id = ?", (clan_id,))
        clan_name = cursor.fetchone()[0]
        clan_text = f"<b>{clan_name}</b> ✔\n👤 Должность: <b>{clan_status}</b>"

    else:
        clan_text = "отсутствует ❌"

    text_message = [f"Информация об игроке <a href='tg://user?id={user_id}'>{name_bot}</a>:",
                    f"━━━━━━━━━━━━━━━",
                    f"📜 Ник в профиле: <b>{name_profile}</b>",
                    f"🔢 Возраст: <u>{age}</u>",
                    f"⚙ Состояние: <b>{ban_text}</b>",
                    f"━━━━━━━━━━━━━━━",
                    f"💳 Баланс рублей: {rubles:,}₽",
                    f"💲 Баланс долларов: {dollars:,}$",
                    f"💹 Баланс биткоинов: {round(bitcoins, 1):,}₿",
                    f"💰 Общая прибыль: {profit_hour:,}₽",
                    f"━━━━━━━━━━━━━━━",
                    f"🌟 Статус <b><u>PREMIUM</u></b>: {premium_status}",
                    f"━━━━━━━━━━━━━━━",
                    f"📜 Клан: {clan_text}",
                    f"━━━━━━━━━━━━━━━",
                    f"🔗 Реферальный уровень: {referal_level}",
                    f"👥 Приглашено людей: {referal_all}"]

    text_message = "\n".join(text_message)

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏢 Список бизнесов", callback_data=f"{user_id}_{callback.from_user.id}")
            ]
        ]
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text_message,
        reply_markup=inline_kb
    )
