import os
import random
import time
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    FSInputFile,
)

from __init__ import *  # подключение к БД

my_business = Router()


def render_xp_bar(xp: int, length: int = 10) -> str:
    if xp < 0:
        xp = 0
    if xp > 100:
        xp = 100
    filled = int(xp / 100 * length)
    empty = length - filled
    return "#" * filled + "_" * empty


# ====== ВСПОМОГАТЕЛЬНЫЕ РЕНДЕРЫ ======
async def render_businesses(user_id: int, message: Message | CallbackQuery):
    """
    Рендер списка всех бизнесов (текст + кнопки).
    """
    cursor.execute(
        "SELECT * FROM business WHERE user_id = ? ORDER BY business_id ASC",
        (user_id,),
    )
    result = cursor.fetchall()

    if not result:
        text = "У тебя пока нет бизнеса 🏚\n\nПопробуй купить первый!"
        if isinstance(message, Message):
            await message.reply(text)
        else:
            await message.message.edit_text(text)
        return

    now_time = int(time.time())
    business_texts = []
    keyboard = []

    cursor.execute(
        "SELECT premium_status FROM game WHERE user_id = ?",
        (user_id,),
    )
    premium_status = cursor.fetchone()[0]

    for (
            b_user_id,
            business_id,
            business_name,
            business_level,
            business_stars,
            business_profit_hour,
            business_balance,
            business_last_time,
            business_exp,
            business_bitcoin_profit,
    ) in result:

        info_button = InlineKeyboardButton(
            text=f"ℹ️ {business_id} Информация",
            callback_data=f"info_business_{business_id}_{user_id}",
        )

        if now_time - int(business_last_time) >= 3600:
            business_profit = "✔️ Доступно к сбору!"
            collect_button = InlineKeyboardButton(
                text="💳 Собрать",
                callback_data=f"collect_one_{business_id}_{user_id}",
            )

        else:
            minutes_left = max(0, (int(business_last_time) + 3600 - now_time) // 60)
            business_profit = f"⏳ Через {minutes_left} мин."
            collect_button = InlineKeyboardButton(
                text=business_profit,
                callback_data="collect_all_",
            )

        if premium_status == "True":
            premium_text = f" x 3 = <u><b>{business_profit_hour * 3:,}</b></u>"

        else:
            premium_text = ""

        business_texts.append(
            f"<u>{business_id}</u>. <b>{business_name}</b>\n"
            f"💸 Прибыль в рублях: {business_profit_hour:,}{premium_text}₽/ч\n"
            f"💹 Прибыль в биткоинах: {business_bitcoin_profit:,}₿/ч\n"
            f"<b>ОСОБЫЕ УЛУЧШЕНИЯ</b>\n"
            f"✨ Уровень: {business_level}\n"
            f"⭐️ Звёзды: {business_stars}\n"
            f"━━━━━━━━━━━━━━━"
        )

        keyboard.append([info_button, collect_button])

    cursor.execute("SELECT rubles FROM game WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    user_rubles = result[0] if result else 0
    balance_pretty = f"{user_rubles:,}".replace(",", ".")
    business_texts.append(f"💸 Твой баланс: <u>{balance_pretty}</u> рублей")

    keyboard.append(
        [InlineKeyboardButton(text="🚀 Собрать всё", callback_data=f"collect_all_{user_id}")]
    )

    text_message = "\n\n".join(business_texts)

    if isinstance(message, Message):
        await message.answer(
            text_message, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        original = message.message

        if original.photo:
            await bot.send_message(
                chat_id=message.message.chat.id, text=text_message,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )

        else:
            await message.message.edit_text(
                text_message, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )


def get_business_info_markup(business_id: int, user_id: int):
    """
    Возвращает caption и клавиатуру для бизнеса.
    """
    cursor.execute(
        "SELECT business_name, business_level, business_stars, business_profit_hour, business_exp, business_last_time, business_bitcoin_profit "
        "FROM business WHERE user_id = ? AND business_id = ?",
        (user_id, business_id),
    )
    result = cursor.fetchone()

    cursor.execute(
        "SELECT premium_status "
        "FROM game WHERE user_id = ?",
        (user_id,),
    )
    premium_status = cursor.fetchone()[0]

    if not result:
        return None, None

    name, level, stars, profit_hour, exp, last_time, bitcoin_profit = result
    now_time = int(time.time())

    # Сбор прибыли
    if now_time - int(last_time) >= 3600:
        collect_button = InlineKeyboardButton(
            text="💳 Собрать", callback_data=f"collect_in_info_{business_id}_{user_id}"
        )
        collect_text = "✔️ Доступно к сбору!"
    else:
        minutes_left = max(0, (int(last_time) + 3600 - now_time) // 60)
        hours_left = minutes_left // 60
        minutes_left = minutes_left % 60
        collect_button = InlineKeyboardButton(
            text=f"⏳ {hours_left} ч. {minutes_left} мин.", callback_data="none"
        )
        collect_text = f"⏳ Через {hours_left} ч. {minutes_left} мин."

    # Улучшение
    if exp >= 100:
        emodz = "✔"
    else:
        emodz = "❌"

    up_kb = InlineKeyboardButton(
        text=f"{emodz} Улучшить бизнес",
        callback_data=f"business_up_{business_id}_{int(level) + 1}_{user_id}",
    )

    # Звезды
    if int(level) >= 5 and stars == 0:
        stars_kb = InlineKeyboardButton(
            text="⭐ Приобрести звезду",
            callback_data=f"buy_stars_{business_id}_{user_id}",
        )
    else:
        stars_kb = InlineKeyboardButton(
            text="❌ Приобрести звезду",
            callback_data=f"not_buy_stars_{business_id}_{user_id}",
        )

    # Назад
    back_kb = InlineKeyboardButton(
        text="◀ Назад",
        callback_data=f"my_business_{user_id}"
    )

    keyboard = [[collect_button, up_kb], [stars_kb, back_kb]]

    price = int(business_id) * 100000 * (int(level) * 10)

    if premium_status == "True":
        premium_text = f" x 3 = <u><b>{profit_hour * 3:,}</b></u>"

    else:
        premium_text = ""

    caption = (
        f"ℹ️ <b>Информация о бизнесе</b>\n\n"
        f"🏢 Название: {name}\n"
        f"💸 Прибыль в рублях: {profit_hour:,}{premium_text}₽/ч\n"
        f"💹 Прибыль в биткоинах: {bitcoin_profit:,}₿/ч\n"
        f"💳 Состояние: {collect_text}\n\n"
        f"✨ Уровень: {level}\n"
        f"⚡ Опыт:\n{render_xp_bar(exp)} ({exp})\n"
        f"{'✔️' if exp >= 100 else '❌'} Стоимость улучшения {price:,}$\n"
        f"⭐️ Звёзды: {stars}\n"
    )

    return caption, InlineKeyboardMarkup(inline_keyboard=keyboard)


# ====== ХЕНДЛЕРЫ ======
@my_business.message(Command("my_business"))
@my_business.callback_query(F.data.startswith("my_business"))
@my_business.message(F.text.casefold() == "мой бизнес")
async def cmd_my_business(message: Message | CallbackQuery):
    await render_businesses(message.from_user.id, message)


async def render_business_info(callback: CallbackQuery, user_id: int, business_id: int):
    """
    Редактирует caption у фото (если уже есть сообщение с фото бизнеса).
    """
    caption, keyboard = get_business_info_markup(business_id, user_id)
    if not caption:
        await callback.answer("❌ Бизнес не найден.", show_alert=True)
        return

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=keyboard,
    )


@my_business.callback_query(F.data.startswith("info_business_"))
async def show_business_info(callback: CallbackQuery):
    """
    Отправляем новое сообщение с фото и caption.
    """
    _, _, business_id_str, user_id_str = callback.data.split("_", 3)
    business_id = int(business_id_str)
    user_id = int(user_id_str)

    caption, keyboard = get_business_info_markup(business_id, user_id)
    if not caption:
        await callback.answer("❌ Бизнес не найден.", show_alert=True)
        return

    media_file = f"image/business_{business_id}.png"
    photo = FSInputFile(media_file, filename=os.path.basename(media_file))

    await callback.message.answer_photo(
        photo=photo,
        caption=caption,
        reply_markup=keyboard,
    )


@my_business.callback_query(F.data.startswith("collect_"))
async def collect_business(callback: CallbackQuery):
    """
    Универсальный сбор бизнеса (по одному, из инфо, или со всех).
    """
    parts = callback.data.split("_")

    now_time = int(time.time())

    # ====== СО ВСЕХ ======
    if parts[1] == "all":
        user_id = int(parts[2])

        cursor.execute(
            "SELECT business_id, business_balance, business_profit_hour, business_last_time, business_exp, business_bitcoin_profit "
            "FROM business WHERE user_id = ?",
            (user_id,),
        )
        businesses = cursor.fetchall()

        cursor.execute(
            "SELECT premium_status "
            "FROM game WHERE user_id = ?",
            (user_id,),
        )
        premium_status = cursor.fetchone()[0]

        total_rubles = 0
        total_bitcoins = 0

        for business_id, balance, profit_hour, last_time, exp, bitcoin_profit in businesses:
            if now_time - int(last_time) >= 3600:
                total_rubles += profit_hour + balance
                total_bitcoins += bitcoin_profit

                if exp < 100:
                    random_exp = random.randint(1, 10)
                    cursor.execute(
                        "UPDATE business SET business_balance = 0, business_last_time = ?, business_exp = ? "
                        "WHERE user_id = ? AND business_id = ?",
                        (now_time, exp + random_exp, user_id, business_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE business SET business_balance = 0, business_last_time = ? "
                        "WHERE user_id = ? AND business_id = ?",
                        (now_time, user_id, business_id),
                    )

        if total_rubles > 0 or total_bitcoins > 0:
            cursor.execute("SELECT rubles, bitcoins FROM game WHERE user_id = ?", (user_id,))
            rubles, bitcoins = cursor.fetchone()

            if premium_status == "True":
                rubles = rubles + (total_rubles * 3)
                total_rubles = total_rubles * 3

            else:
                rubles = rubles + total_rubles


            cursor.execute(
                "UPDATE game SET rubles = ?, bitcoins = ? WHERE user_id = ?",
                (rubles, bitcoins + total_bitcoins, user_id,),
            )
            conn.commit()

            await callback.answer(
                f"🚀 Собрано со всех бизнесов:\n"
                f"{total_rubles:,}₽\n"
                f"{total_bitcoins}₿", show_alert=True
            )
        else:
            await callback.answer("❌ Сейчас нечего собирать", show_alert=True)
            return

        await render_businesses(user_id, callback)
        return

    # ====== ОДИН БИЗНЕС (one или in_info) ======
    if parts[1] == "one":
        business_id = int(parts[2])
        user_id = int(parts[3])
    elif parts[1] == "in":
        business_id = int(parts[3])
        user_id = int(parts[4])
    else:
        await callback.answer("❌ Неверные данные.", show_alert=True)
        return

    cursor.execute(
        "SELECT business_balance, business_profit_hour, business_last_time, business_exp, business_bitcoin_profit "
        "FROM business WHERE user_id = ? AND business_id = ?",
        (user_id, business_id),
    )
    row = cursor.fetchone()

    cursor.execute(
        "SELECT premium_status "
        "FROM game WHERE user_id = ?",
        (user_id,),
    )
    premium_status = cursor.fetchone()[0]

    if not row:
        await callback.answer("❌ Бизнес не найден.", show_alert=True)
        return

    balance, profit_hour, last_time, exp, bitcoin_profit = row

    if now_time - int(last_time) < 3600:
        await callback.answer("❌ Прибыль ещё не накопилась.", show_alert=True)
        if callback.message.photo:
            await render_business_info(callback, user_id, business_id)
        else:
            await render_businesses(user_id, callback)
        return

    collected_rubles = profit_hour + balance
    collected_bitcoins = bitcoin_profit

    if exp < 100:
        random_exp = random.randint(1, 10)
        cursor.execute(
            "UPDATE business SET business_balance = 0, business_last_time = ?, business_exp = ? "
            "WHERE user_id = ? AND business_id = ?",
            (now_time, exp + random_exp, user_id, business_id),
        )
    else:
        cursor.execute(
            "UPDATE business SET business_balance = 0, business_last_time = ? "
            "WHERE user_id = ? AND business_id = ?",
            (now_time, user_id, business_id),
        )

    cursor.execute("SELECT rubles, bitcoins FROM game WHERE user_id = ?", (user_id,))
    rubles, bitcoins = cursor.fetchone()

    if premium_status == "True":
        rubles = rubles + (collected_rubles * 3)
        collected_rubles = collected_rubles * 3
    else:
        rubles = rubles + collected_rubles

    cursor.execute(
        "UPDATE game SET rubles = ?, bitcoins = ? WHERE user_id = ?",
        (rubles, bitcoins + collected_bitcoins, user_id,),
    )
    conn.commit()

    await callback.answer(
        f"🚀 Ты собрал прибыль:\n"
        f"{collected_rubles:,}₽\n"
        f"{collected_bitcoins}₿", show_alert=True
    )

    if callback.message.photo:
        await render_business_info(callback, user_id, business_id)
    else:
        await render_businesses(user_id, callback)
