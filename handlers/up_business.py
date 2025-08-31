from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *

up_business = Router()


@up_business.message(Command(commands="up_business"))
@up_business.message(F.text.casefold() == "улучшить бизнес")
async def cmd_up_business(message: Message):
    cursor.execute(
        "SELECT business_id, business_name, business_level, business_exp "
        "FROM business "
        "WHERE user_id = ? AND business_exp > 30 AND business_level = 1 "
        "ORDER BY business_id ASC",
        (message.from_user.id,)
    )
    result = cursor.fetchall()

    if not result:
        await message.reply("❌ У вас либо нет бизнеса, либо опыта бизнеса недостаточно!")
        return

    cursor.execute("SELECT rubles, dollars FROM game WHERE user_id = ?", (message.from_user.id,))
    result_2 = cursor.fetchone()
    rubles, dollars = result_2

    text_message = ["⚡️ Ваши бизнесы с возможностью улучшения:\n"]

    in_keyboard = []
    row = []

    for idx, (business_id, business_name, business_level, business_exp) in enumerate(result, start=1):
        price = business_id * 100000 * (int(business_level) * 10)

        if int(dollars) >= int(price):
            emodz = "✔️"

        else:
            emodz = "❌"

        text_message.append(
            f"<b>{business_id}. {business_name}</b>\n"
            f"✨ Уровень: <u>{business_level}</u>\n"
            f"{emodz} Улучшить: <u>{price:,}</u><b>$</b>\n"
        )

        up_button = InlineKeyboardButton(
            text=f"📈 {business_id} Улучшить",
            callback_data=f"business_up_{business_id}_{int(business_level)+1}_{message.from_user.id}",
        )

        row.append(up_button)

        if idx % 3 == 0:  # каждые 3 кнопки — новая строка
            in_keyboard.append(row)
            row = []

    # если остались кнопки (менее 3 в конце) — добавляем строку
    if row:
        in_keyboard.append(row)

    text_message.append("Для улучшения нажмите на кнопку с нужным ID бизнеса")
    text_message = "\n".join(text_message)

    await message.reply(
        text_message,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=in_keyboard)
    )


@up_business.callback_query(F.data.startswith("business_up_"))
async def button_up_business(callback: CallbackQuery):
    action = callback.data.split("_")
    business_id = int(action[2])
    business_new_level = int(action[3])
    user_id = int(action[4])

    cursor.execute("SELECT business_name, business_level, business_profit_hour FROM business WHERE business_id = ? AND user_id = ?", (business_id, user_id,))
    result = cursor.fetchone()
    business_name = result[0]
    business_level = int(result[1])
    business_profit_hour = int(result[2])

    cursor.execute("SELECT dollars, profit_hour FROM game WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    dollars = int(result[0])
    profit_hour = result[1]

    if int(business_level) >= int(business_new_level):
        await callback.answer(show_alert=True, text="❌ Эта кнопка неактуальна! Уровень вашего бизнеса уже выше или равен желаемому улучшению")
        return

    price = int(business_id) * 100000 * (int(business_level) * 10)

    if int(dollars) < int(price):
        await callback.answer(f"❌ У вас недостаточно долларов! ({dollars:,}/{price:,})")
        return

    cursor.execute("UPDATE game SET dollars = ? WHERE user_id = ?", (dollars-price, user_id,))
    conn.commit()

    business_profit_hour_new = business_profit_hour * 3
    business_bitcoin_profit_new = business_new_level * 0.1 * business_id

    cursor.execute("UPDATE business SET business_level = ?, business_profit_hour = ?,  business_exp = '0', business_bitcoin_profit = ? WHERE user_id = ? AND business_id = ?", (business_new_level, business_profit_hour_new, business_bitcoin_profit_new, user_id, business_id,))
    conn.commit()

    cursor.execute(
        "UPDATE game SET profit_hour = ? WHERE user_id = ?",
        (profit_hour-business_profit_hour+business_profit_hour_new, callback.from_user.id,))
    conn.commit()

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀ Назад",
                                     callback_data=f"info_business_{business_id}_{callback.from_user.id}")
            ]
        ]
    )

    text = f"✔ Вы успешно улучшили свой бизнес <b>{business_name}</b> до <u>{business_new_level}</u> уровня!\n"\
           f"₿ Теперь твой бизнес приносит {business_new_level*0.1*business_id} BTC/ч!\n"\
           f"Проверить доход можно по команде:\n"\
           f"/my_business → «<b>ℹ {business_id} Информация</b>»"

    if callback.message.photo:
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=text,
            reply_markup=inline_kb
        )

    else:
        await bot.edit_message_text(
            message_id=callback.message.message_id,
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=inline_kb
        )
