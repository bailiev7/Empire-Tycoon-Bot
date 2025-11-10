import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *  # подключение к БД

promo = Router()


@promo.message(F.text.casefold().startswith("промо"))
async def cmd_promo(message: Message):
    if message.text == "промо":
        await message.reply("❌ Введите нужный промокод!")
        return

    promo_code = message.text.split()[1]

    cursor.execute("SELECT promo_activate, promo_reward, promo_reward_type FROM promo WHERE promo_code = ?", (promo_code,))
    result = cursor.fetchone()

    if not result:
        await message.reply("❌ Такого промокода не существует!")
        return

    promo_activate, promo_reward, promo_reward_type = result

    if promo_activate == 0:
        await message.reply("❌ Активации промокода закончились")
        return

    cursor.execute("SELECT promo_code FROM promo_active WHERE promo_code = ? AND user_id = ?", (promo_code, message.from_user.id,))
    result = cursor.fetchone()

    if result:
        await message.reply("❌ Вы уже вводили данный промокод!")
        return

    cursor.execute(f"SELECT {promo_reward_type} FROM game WHERE user_id = ?", (message.from_user.id,))
    money_type = cursor.fetchone()[0]

    cursor.execute(f"UPDATE game SET {promo_reward_type} = ? WHERE user_id = ?", (money_type+promo_reward, message.from_user.id,))
    conn.commit()

    if promo_reward_type == "rubles":
        reward_text = "₽"

    elif promo_reward_type == "dollars":
        reward_text = "$"

    elif promo_reward_type == "bitcoins":
        reward_text = "₿"

    cursor.execute("UPDATE promo SET promo_activate = ? WHERE promo_code = ?", (promo_activate-1, promo_code,))
    conn.commit()
    cursor.execute(
        "INSERT INTO promo_active(promo_code, user_id) VALUES(?, ?)",
        (promo_code, message.from_user.id,)
    )
    conn.commit()

    await message.reply(f"✔ Вы успешно активировали промокод и получили:\n"
                        f"💰 {promo_reward:,}{reward_text}\n\n"
                        f"💳 Баланс: {money_type+promo_reward:,}{reward_text}")
