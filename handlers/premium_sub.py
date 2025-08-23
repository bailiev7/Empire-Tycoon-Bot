import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message

from __init__ import *  # подключение к БД

premium_sub = Router()


@premium_sub.message(F.text.casefold() == "премиум")
@premium_sub.message(Command(commands="premium"))
async def cmd_premium_sub(message: Message):
    cursor.execute("SELECT bitcoins, premium_status, premium_until FROM game WHERE user_id = ?", (message.from_user.id,))
    bitcoins, premium_status, premium_until = cursor.fetchone()

    if premium_status == "True":
        now = int(time.time())
        remaining = premium_until - now

        days = remaining // 86400  # 1 день = 86400 секунд
        hours = (remaining % 86400) // 3600  # остаток после деления на дни / 3600

        await message.reply(f"✔ Подписка <b><u>PREMIUM</u></b> активна!\n"
                            f"Она действует ещё {days} д {hours} ч.")
        return

    if bitcoins < 10:
        await message.reply(f"❌ У вас недостаточно BTC! ({round(bitcoins, 1)}/10)")
        return
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Приобрести PREMIUM", callback_data=f"buy_premium_{message.from_user.id}"),
                InlineKeyboardButton(text="Посмотреть преимущества", callback_data=f"what_in_premium_{message.from_user.id}")
            ]
        ]
    )

    await message.reply("❌ У вас нет подписки!\n"
                        "ℹ Вы уверены что хотите приобрести <b><u>PREMIUM</u></b> за 10₿?", reply_markup=inline_kb)


@premium_sub.callback_query(F.data.startswith("buy_premium_"))
async def button_up_business(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = action[2]

    cursor.execute("SELECT bitcoins FROM game WHERE user_id = ?", (user_id,))
    bitcoins = cursor.fetchone()[0]

    if bitcoins < 10:
        await callback.answer(f"❌ У вас недостаточно BTC! ({bitcoins}/10)")
        return

    # Текущее время в секундах
    now = int(time.time())

    # Добавляем 30 дней (30 * 24 * 60 * 60 секунд)
    premium_until = now + 30 * 24 * 60 * 60

    cursor.execute("UPDATE game SET bitcoins = ?, premium_status = 'True', premium_until = ? WHERE user_id = ?", (round(bitcoins-10, 1), premium_until, user_id,))
    conn.commit()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="✔ Поздравляем с покупкой премиума!\n"
             "⌛ Срок действия: 30 дней\n"
             "📈 С преимуществами можно ознакомиться по команде <b><u>/premium</u></b>"
    )

