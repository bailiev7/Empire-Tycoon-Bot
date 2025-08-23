from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
import time

from __init__ import *

business = Router()  # [1]


def db_table_business(user_id, business_id, business_name,
                      business_profit_hour, business_last_time):
    cursor.execute("INSERT INTO business (user_id, business_id, business_name, "
                   "business_profit_hour, business_last_time) VALUES (?, ?, ?, ?, ?)",
                   (user_id, business_id, business_name,
                    business_profit_hour, business_last_time))
    conn.commit()


@business.message(Command(commands="business"))  # [2]
async def cmd_business(message: Message):
    cursor.execute("SELECT tutorial FROM game WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    tutorial = result[0]

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Приобрести бизнес", callback_data=f"buy_1_business_{message.from_user.id}")
            ]
        ]
    )

    if tutorial == 0:
        await message.reply(f"У вас сейчас нет бизнеса, ваш доход в час составляет: 0 рублей. 😮\n\n"
                            f"У вас на балансе 250.000 рублей, этого хватает для покупки вашего первого бизнеса - шаурмечная! 🌭\n"
                            f"Вы можете нажать кнопку ниже для приобретения",
                            reply_markup=inline_kb)

    elif tutorial == 3:
        await message.reply("")

    else:
        await message.reply("❌ Вы сейчас на другом этапе обучения!")


@business.callback_query(F.data.startswith("buy_1_business_"))
async def callbacks_num(callback: CallbackQuery):
    action = callback.data.split("_")

    user_id = action[3]

    cursor.execute("SELECT rubles FROM game WHERE user_id == ?", (user_id,))
    result = cursor.fetchone()

    rubles = result[0]
    if rubles < 250000:
        await callback.answer("❌ У вас недостаточно средств!")
        return

    cursor.execute("UPDATE game SET rubles = ?, profit_hour = '20000' tutorial = '1' WHERE user_id = ?",
                   (rubles - 250000, callback.from_user.id,))
    conn.commit()

    now_time = int(time.time())

    db_table_business(callback.from_user.id, 1, "Шаурмечная", 20000, now_time)

    await callback.message.edit_text("✔ Вы успешно приобрели свой первый бизнес. Поздравляем! 🎉\n"
                                     "Ваша прибыль в час составляет: 20.000 рублей 🤑\n\n\n"
                                     "Так же вы можете получать деньги за фарм. Отправляйте команду «Фарм» для получения 💸")
