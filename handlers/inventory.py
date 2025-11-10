import time
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from __init__ import *  # подключение к БД
from handlers.case_shop import CASES, open_case_for_user  # импорт кейсов и функции открытия

inventory = Router()


# ---------------------- Команда /инвентарь ---------------------- #
@inventory.message(F.text.casefold() == "инвентарь")
@inventory.message(Command(commands="inventory"))
async def cmd_inventory(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT item_type, value, amount FROM inventory WHERE user_id = ?", (user_id,))
    items = cursor.fetchall()

    if not items:
        await message.answer("🎒 Ваш инвентарь пуст.")
        return

    text_lines = ["🎒 <b>Ваш инвентарь:</b>\n"]
    kb = InlineKeyboardBuilder()

    for item_type, value, amount in items:
        if amount <= 0:
            continue  # не показываем пустые слоты

        # ---------------------- VIP ---------------------- #
        if item_type == "vip":
            days = value.replace("day", "")
            text_lines.append(f"⭐ <u><b>PREMIUM</b></u> на {days} дн. — <u>{amount} шт.</u>")
            kb.add(
                InlineKeyboardButton(
                    text=f"Активировать PREMIUM {days} дн. ({amount} шт.)",
                    callback_data=f"activate_vip_{days}_{user_id}"
                )
            )

        # ---------------------- Токены ---------------------- #
        elif item_type == "token":
            if value == "nick_change":
                text_lines.append(f"🎭 Токен смены ника — <u>{amount} шт.</u>")
            elif value == "clan_slot":
                text_lines.append(f"🏰 Токен на клан — <u>{amount} шт.</u>")

        # ---------------------- Кейсы ---------------------- #
        elif item_type == "case":
            case_id = int(value)
            case_info = CASES.get(case_id, {"name": f"Неизвестный кейс {case_id}"})
            case_name = case_info["name"]
            text_lines.append(f"{case_name} — <u>{amount} шт.</u>")
            kb.add(
                InlineKeyboardButton(
                    text=f"Открыть {case_name} ({amount} шт.)",
                    callback_data=f"open_case_{case_id}_{user_id}"
                )
            )

        else:
            text_lines.append(f"❓ {item_type} ({value}) — {amount} шт.")

    kb.adjust(2)

    if text_lines == ["🎒 <b>Ваш инвентарь:</b>\n"]:
        text_lines = ["🎒 <b>Ваш инвентарь</b> пуст!"]

    await message.answer(
        text="\n".join(text_lines),
        reply_markup=kb.as_markup() if kb else None
    )


# ---------------------- Активация VIP ---------------------- #
@inventory.callback_query(F.data.startswith("activate_vip_"))
async def callback_activate_vip(callback: CallbackQuery):
    _, _, days, user_id_str = callback.data.split("_")
    days = int(days)
    user_id = int(user_id_str)

    cursor.execute("SELECT amount FROM inventory WHERE user_id=? AND item_type='vip' AND value=?",
                   (user_id, f"{days}day"))
    result = cursor.fetchone()
    if not result or result[0] <= 0:
        await callback.answer("❌ У вас нет такого VIP-токена!", show_alert=True)
        return

    cursor.execute("UPDATE inventory SET amount = amount - 1 WHERE user_id=? AND item_type='vip' AND value=?",
                   (user_id, f"{days}day"))

    cursor.execute("SELECT premium_until FROM game WHERE user_id=?", (user_id,))
    premium_until = cursor.fetchone()[0] or int(time.time())
    new_premium = max(int(time.time()), premium_until) + days * 86400
    cursor.execute("UPDATE game SET premium_status='True', premium_until=? WHERE user_id=?",
                   (new_premium, user_id))
    conn.commit()

    remaining_seconds = new_premium - int(time.time())
    premium_days = remaining_seconds // 86400
    premium_hours = (remaining_seconds % 86400) // 3600

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"⭐ <u><b>PREMIUM</b></u> на {days} дн. активирован!\n"
             f"⌛ Осталось {premium_days} дн {premium_hours} ч"
    )


# ---------------------- Открытие кейсов ---------------------- #
@inventory.callback_query(F.data.startswith("open_case_"))
async def callback_open_case(callback: CallbackQuery):
    _, _, case_id_str, user_id_str = callback.data.split("_")
    case_id = int(case_id_str)
    user_id = int(user_id_str)

    cursor.execute("SELECT amount FROM inventory WHERE user_id=? AND item_type='case' AND value=?",
                   (user_id, str(case_id)))
    result = cursor.fetchone()
    if not result or result[0] <= 0:
        await callback.answer("❌ У вас нет такого кейса!", show_alert=True)
        return

    cursor.execute("UPDATE inventory SET amount = amount - 1 WHERE user_id=? AND item_type='case' AND value=?",
                   (user_id, str(case_id)))
    conn.commit()

    await open_case_for_user(case_id, user_id, callback.message.chat.id)
