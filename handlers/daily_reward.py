import time
import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from __init__ import *  # подключение к БД

daily_reward = Router()


def choose_reward():
    rewards = [
        {"type": "rubles", "min": 10_000, "max": 100_000, "weight": 40},
        {"type": "dollars", "min": 500, "max": 2000, "weight": 25},
        {"type": "premium_day", "days": 1, "weight": 5},
        {"type": "bitcoins", "min": 1, "max": 50, "div": 100, "weight": 2},  # 0.01 - 0.5 BTC
        {"type": "case", "case_name": "📦 Обычный кейс", "case_id": 1, "weight": 100},
    ]

    total_weight = sum(r["weight"] for r in rewards)
    rnd = random.randint(1, total_weight)
    cur = 0
    for reward in rewards:
        cur += reward["weight"]
        if rnd <= cur:
            return reward


def choose_amount(reward):
    if reward["type"] == "rubles":
        return random.randint(int((reward["min"] + reward["max"]) / 2), reward["max"])
    elif reward["type"] == "dollars":
        return random.randint(int((reward["min"] + reward["max"]) / 2), reward["max"])
    elif reward["type"] == "bitcoins":
        return round(random.randint(reward["min"], reward["max"]) / reward["div"], 2)
    return None


@daily_reward.message(F.text.casefold() == "бонус")
@daily_reward.message(Command(commands="bonus"))
async def cmd_daily_reward(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT rubles, dollars, bitcoins, premium_status, premium_until, daily_reward_until FROM game WHERE user_id = ?", (user_id,))
    rub, usd, btc, premium_status, premium_until, daily_reward_until = cursor.fetchone()

    now_time = int(time.time())

    # проверка премиума
    if premium_status == "True" and premium_until > now_time:
        cooldown = 2 * 3600  # 2 часа
        info_text = "⭐ У вас есть <b><u>PREMIUM</u></b>! Бонус можно получать раз в 2 часа."
    else:
        cooldown = 6 * 3600  # 6 часов
        info_text = "⏳ Бонус можно получать раз в 6 часов."

    if now_time < daily_reward_until:
        left = daily_reward_until - now_time
        hours = left // 3600
        minutes = (left % 3600) // 60
        await message.answer(f"⏳ Вы уже получили бонус.\nДо следующего: <b>{hours}ч {minutes}м</b>\n\n{info_text}")
        return

    # выбор награды
    reward = choose_reward()
    msg = "🎁 Вы получили: "

    if reward["type"] == "rubles":
        val = choose_amount(reward)
        rub += val
        msg += f"<b>{val:,}₽</b>"

    elif reward["type"] == "dollars":
        val = choose_amount(reward)
        usd += val
        msg += f"<b>{val:,}$</b>"

    elif reward["type"] == "bitcoins":
        val = choose_amount(reward)
        btc += val
        msg += f"<b>{val}₿</b>"

    elif reward["type"] == "premium_day":
        days = reward["days"]

        # Проверяем, есть ли уже премиум-токен в инвентаре
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

        msg += f"⭐ <u><b>PREMIUM</b></u> токен {days} дн."

    elif reward["type"] == "case":
        case_name = reward["case_name"]
        case_id = reward["case_id"]
        cursor.execute(
            "SELECT amount FROM inventory WHERE user_id=? AND item_type='case' AND value=?",
            (user_id, case_id)
        )
        row = cursor.fetchone()
        if row:
            if row[0] < 3:
                cursor.execute(
                    "UPDATE inventory SET amount=? WHERE user_id=? AND item_type='case' AND value=?",
                    (row[0] + 1, user_id, case_id)
                )
                msg += f"📦 {case_name}"
            else:
                msg += f"❌ {case_name} не помещается (макс. 3 шт.)"
        else:
            cursor.execute(
                "INSERT INTO inventory(user_id, item_type, value, amount) VALUES(?, 'case', ?, 1)",
                (user_id, case_id)
            )
            msg += f"📦 {case_name}"

    # обновляем валюты
    cursor.execute(
        "UPDATE game SET rubles=?, dollars=?, bitcoins=?, daily_reward_until=? WHERE user_id=?",
        (rub, usd, btc, now_time + cooldown, user_id)
    )
    conn.commit()

    cursor.execute("SELECT tutorial FROM game WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    tutorial = result[0]

    if tutorial == 5:
        cursor.execute("UPDATE game SET tutorial = '6' WHERE user_id = ?", (message.from_user.id,))
        conn.commit()

        await message.reply(msg + f"\n\n{info_text}\n\n"
                                  f"📜 Здесь каждые 6 часов ты сможешь получать различные бонусы: от рублей до кейсов и биткоинов. \n\n"
                                  f"Следующий этап - обмен валют. Введи команду <b><u>/dollars</u></b>")
        return

    await message.reply(msg + f"\n\n{info_text}")
