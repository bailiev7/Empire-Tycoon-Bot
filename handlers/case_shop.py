import time
import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from __init__ import *  # подключение к БД и bot

case_shop = Router()

# ---------------------- Кейсы ---------------------- #
CASES = {
    1: {  # 📦 Рублёвый кейс
        "name": "📦 Рублёвый кейс",
        "price": 100_000,
        "currency": "rubles",
        "rewards": [
            {"type": "rubles", "min": 50_000, "max": 120_000, "weight": 60},
            {"type": "rubles", "min": 150_000, "max": 300_000, "weight": 30},
            {"type": "dollars", "min": 1_000, "max": 10_000, "weight": 8},
            {"type": "nick_change", "weight": 2},
        ],
    },
    2: {  # 🎁 Долларовый кейс
        "name": "🎁 Долларовый кейс",
        "price": 500_000,
        "currency": "dollars",
        "rewards": [
            {"type": "dollars", "min": 150_000, "max": 600_000, "weight": 77},
            {"type": "dollars", "min": 800_000, "max": 2_000_000, "weight": 10},
            {"type": "dollars", "min": 5_000_000, "max": 10_000_000, "weight": 6},
            {"type": "bitcoins", "min": 0.05, "max": 0.3, "weight": 4},
            {"type": "vip", "days": random.choice([1, 2, 3]), "weight": 3},
        ],
    },
    3: {  # 🌌 Биткоиновый кейс
        "name": "🌌 Биткоиновый кейс",
        "price": 1,
        "currency": "bitcoins",
        "rewards": [
            {"type": "bitcoins", "min": 0.3, "max": 1.0, "weight": 70},
            {"type": "bitcoins", "min": 1.5, "max": 3.0, "weight": 15},
            {"type": "bitcoins", "min": 5, "max": 5, "weight": 5},
            {"type": "bitcoins", "min": 10, "max": 10, "weight": 5},
            {"type": "vip", "days": random.choice([3, 7, 15]), "weight": 3},
            {"type": "clan_slot", "weight": 2},
        ],
    },
}

# ---------------------- Функции открытия ---------------------- #
def choose_reward(case_id: int):
    rewards = CASES[case_id]["rewards"]
    total_weight = sum(r["weight"] for r in rewards)
    rnd = random.uniform(0, total_weight)
    upto = 0
    for r in rewards:
        if upto + r["weight"] >= rnd:
            return r
        upto += r["weight"]
    return rewards[-1]

def choose_amount(reward: dict):
    if reward.get("min") == reward.get("max"):
        return reward["min"]
    roll = random.random()
    if isinstance(reward.get("min"), float) or isinstance(reward.get("max"), float):
        if roll < 0.7:
            return round(random.uniform(reward["min"], (reward["min"] + reward["max"]) / 2), 2)
        elif roll < 0.95:
            return round(random.uniform((reward["min"] + reward["max"]) / 2, reward["max"]), 2)
        else:
            return round(reward["max"], 2)
    else:
        if roll < 0.7:
            return random.randint(reward["min"], int((reward["min"] + reward["max"]) / 2))
        elif roll < 0.95:
            return random.randint(int((reward["min"] + reward["max"]) / 2), reward["max"])
        else:
            return reward["max"]


async def open_case_for_user(case_id: int, user_id: int, chat_id: int):
    case = CASES.get(case_id)
    if not case:
        await bot.send_message(chat_id, "❌ Кейс не найден!")
        return

    cursor.execute("SELECT rubles, dollars, bitcoins FROM game WHERE user_id = ?", (user_id,))
    rub, usd, btc = cursor.fetchone()

    reward = choose_reward(case_id)
    msg = f"🎉 Из {case['name']} выпало:\n"

    if reward["type"] in ("rubles", "dollars", "bitcoins"):
        val = choose_amount(reward)
        if reward["type"] == "rubles":
            rub += val
            msg += f"<b>{val:,}₽</b>\n\n💳 Баланс: {rub:,}₽"
        elif reward["type"] == "dollars":
            usd += val
            msg += f"<b>{val:,}$</b>\n\n💳 Баланс: {usd:,}$"
        elif reward["type"] == "bitcoins":
            btc += val
            msg += f"<b>{val}₿</b>\n\n💳 Баланс: {btc:,}₿"
        cursor.execute("UPDATE game SET rubles=?, dollars=?, bitcoins=? WHERE user_id=?",
                       (rub, usd, btc, user_id))
        conn.commit()
    else:
        # Для токенов добавляем в инвентарь
        cursor.execute("SELECT amount FROM inventory WHERE user_id=? AND item_type='token' AND value=?",
                       (user_id, reward["type"]))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE inventory SET amount=? WHERE user_id=? AND item_type='token' AND value=?",
                           (row[0]+1, user_id, reward["type"]))
        else:
            cursor.execute("INSERT INTO inventory(user_id, item_type, value, amount) VALUES (?, 'token', ?, 1)",
                           (user_id, reward["type"]))
        conn.commit()
        msg += f"🎁 {reward['type']} получен!"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Купить ещё", callback_data=f"case_info_{case_id}_{user_id}"),
                InlineKeyboardButton(text="🎁 Открыть ещё", callback_data=f"open_case_{case_id}_{user_id}")
            ],
            [
                InlineKeyboardButton(text="⬅ В магазин", callback_data=f"case_shop_{user_id}")
            ],
        ]
    )
    await bot.send_message(chat_id, msg, reply_markup=kb)


# ---------------------- CALLBACKS ---------------------- #
@case_shop.callback_query(F.data.startswith("case_shop_"))
async def cmd_case_shop(callback: CallbackQuery):
    cursor.execute("SELECT rubles, dollars, bitcoins FROM game WHERE user_id = ?", (callback.from_user.id,))
    rubles, dollars, bitcoins = cursor.fetchone()

    text_message = ["🎁 Доступные кейсы:"]
    builder = InlineKeyboardBuilder()

    for case_id, case in CASES.items():
        price = case["price"]
        cur = case["currency"]
        type_money = {"rubles": "₽", "dollars": "$", "bitcoins": "₿"}[cur]
        text_message.append(f"{case_id}. {case['name']} - {price:,}{type_money}")
        builder.add(
            InlineKeyboardButton(
                text=case["name"],
                callback_data=f"case_info_{case_id}_{callback.from_user.id}"
            )
        )
    builder.adjust(2)
    text_message.append(f"\n💳 Баланс рублей: <u>{rubles:,}</u>₽")
    text_message.append(f"💵 Баланс долларов: <u>{dollars:,}</u>$")
    text_message.append(f"💹 Баланс биткоинов: <u>{round(bitcoins, 1):,}</u>₿")
    await bot.send_message(callback.message.chat.id, "\n".join(text_message), reply_markup=builder.as_markup())


@case_shop.callback_query(F.data.startswith("case_info_"))
async def case_info(callback: CallbackQuery):
    case_id, user_id = map(int, callback.data.split("_")[2:])
    case = CASES.get(case_id)
    if not case:
        await callback.answer("Кейс не найден!", show_alert=True)
        return
    type_money = {"rubles": "₽", "dollars": "$", "bitcoins": "₿"}[case['currency']]
    text = f"{case['name']}\nЦена: {case['price']:,}{type_money}\n\n❓ Купить?"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Купить", callback_data=f"buy_case_{case_id}_{user_id}")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data=f"case_shop_{user_id}")],
        ]
    )
    await bot.send_message(callback.message.chat.id, text, reply_markup=kb)


@case_shop.callback_query(F.data.startswith("buy_case_"))
async def buy_case(callback: CallbackQuery):
    case_id, user_id = map(int, callback.data.split("_")[2:])
    case = CASES.get(case_id)
    cursor.execute("SELECT rubles, dollars, bitcoins FROM game WHERE user_id = ?", (user_id,))
    rub, usd, btc = cursor.fetchone()
    enough = False
    if case["currency"] == "rubles" and rub >= case["price"]:
        rub -= case["price"]
        enough = True
    elif case["currency"] == "dollars" and usd >= case["price"]:
        usd -= case["price"]
        enough = True
    elif case["currency"] == "bitcoins" and btc >= case["price"]:
        btc -= case["price"]
        enough = True
    if not enough:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    cursor.execute("UPDATE game SET rubles=?, dollars=?, bitcoins=? WHERE user_id=?",
                   (rub, usd, btc, user_id))
    cursor.execute("SELECT amount FROM inventory WHERE user_id=? AND item_type='case' AND value=?",
                   (user_id, str(case_id)))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE inventory SET amount=? WHERE user_id=? AND item_type='case' AND value=?",
                       (row[0]+1, user_id, str(case_id)))
    else:
        cursor.execute("INSERT INTO inventory(user_id, item_type, value, amount) VALUES (?, 'case', ?, 1)",
                       (user_id, str(case_id)))
    conn.commit()

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Открыть",
                                     callback_data=f"open_case_{case_id}_{callback.from_user.id}"),
            ]
        ]
    )

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"✅ {case['name']} куплен и добавлен в 🎒 инвентарь!\nОткрой его через команду /inventory",
        reply_markup=inline_kb
    )
