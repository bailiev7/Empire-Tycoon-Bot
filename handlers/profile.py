import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

profile = Router()


@profile.message(F.text.casefold() == "профиль")
@profile.message(Command(commands="profile"))
async def cmd_profile(message: Message | CallbackQuery):
    cursor.execute("SELECT rubles, dollars, bitcoins, profit_hour, premium_status, premium_until FROM game WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    rubles, dollars, bitcoins, profit_hour, premium_status, premium_until = result

    cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    name_user = result[0]

    cursor.execute("SELECT business_id, business_name, business_profit_hour, business_level FROM business WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchall()

    text_message = [f"Профиль <b>{name_user}</b>:\n\n"]

    if premium_status == "True":
        now = int(time.time())
        remaining = premium_until - now

        days = remaining // 86400  # 1 день = 86400 секунд
        premium_status = f"активна ✔ (осталось {days} дн.)"

    else:
        premium_status = "неактивна ❌"

    for business_id, business_name, business_profit_hour, business_level in result:

        text_message.append(
            f"━━━━━━━━━━━━━━━\n"
            f"{business_id}. <b>{business_name}</b>\n"
            f"💸 Прибыль: <u>{business_profit_hour:,}</u> руб/ч\n"
            f"✨ Уровень: {business_level}\n"
        )

    text_message.append(f"━━━━━━━━━━━━━━━\n\n")
    text_message.append(f"💰 Общая прибыль: <u>{profit_hour:,}</u> ₽/ч\n")
    text_message.append(f"💳 Баланс рублей: <u>{rubles:,}</u>₽\n")
    text_message.append(f"💵 Баланс долларов: <u>{dollars:,}</u>$\n")
    text_message.append(f"💹 Баланс биткоинов: <u>{round(bitcoins, 1):,}</u>₿\n")
    text_message.append(f"📈 <u><b>PREMIUM</b></u> подписка: {premium_status}")

    # Клавиатура подтверждения
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍ Изменить данные", callback_data=f"change_date_{message.from_user.id}"),
                InlineKeyboardButton(text="🔗 Реферальная ссылка", callback_data=f"referal_link_{message.from_user.id}")
            ]
        ]
    )

    text_message = "".join(text_message)

    await message.reply(text_message, reply_markup=inline_kb)
