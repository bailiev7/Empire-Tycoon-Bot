import os
import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery

from __init__ import *  # подключение к БД

shop_business = Router()


def db_table_business(user_id, business_id, business_name, business_profit_hour, business_last_time):
    cursor.execute(
        "INSERT INTO business (user_id, business_id, business_name, business_profit_hour, business_last_time) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, business_id, business_name, business_profit_hour, business_last_time)
    )
    conn.commit()


@shop_business.callback_query(F.data.startswith("shop_business_"))
@shop_business.callback_query(F.data.startswith("back_to_shop_"))
@shop_business.message(Command(commands="shop_business"))
@shop_business.message(F.text.casefold() == "магазин бизнесов")
async def cmd_shop_business(message: Message | CallbackQuery):
    cursor.execute(
        "SELECT business_id, business_name, business_price, business_profit_hour "
        "FROM business_info ORDER BY business_id ASC"
    )
    result = cursor.fetchall()

    # собираем список строк для сообщения
    business_texts = []
    for _, name, price, profit in result:
        price_fmt = f"{price:,}".replace(",", ".")
        profit_fmt = f"{profit:,}".replace(",", ".")
        business_texts.append(
            f"<b>{name}</b>\n💰 Цена: <u>{price_fmt}</u>\n📈 Прибыль: <u>{profit_fmt}</u>/час\n"
        )

    cursor.execute("SELECT rubles FROM game WHERE user_id = ?", (message.from_user.id,))
    result2 = cursor.fetchone()
    rubles = result2[0]
    balance_pretty = f"{rubles:,}".replace(",", ".")

    business_texts.append(f"\n💸 Твой баланс: <u>{balance_pretty}</u> рублей")

    text_message = "\n".join(business_texts)

    # строим клавиатуру
    builder = InlineKeyboardBuilder()
    for business_id, business_name, _, _ in result:
        builder.add(
            InlineKeyboardButton(
                text=business_name,
                callback_data=f"business_info_{business_id}_{message.from_user.id}"
            )
        )
    builder.adjust(2)

    if isinstance(message, Message):
        await message.reply(
            text=f"📋 <b>Список бизнесов:</b>\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"{text_message}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        await bot.send_message(
            text=f"📋 <b>Список бизнесов:</b>\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"{text_message}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
            chat_id=message.message.chat.id
        )
    return


@shop_business.callback_query(F.data.startswith("business_info_"))
async def callbacks_business_info_(callback: CallbackQuery):
    action = callback.data.split("_")
    business_id = action[2]
    user_id = action[3]

    cursor.execute(
        "SELECT business_name, business_desc, business_price, business_profit_hour "
        "FROM business_info WHERE business_id = ?", (business_id,))
    result = cursor.fetchone()
    business_name, business_desc, business_price, business_profit_hour = result

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Приобрести бизнес",
                                     callback_data=f"buy_business_{business_id}_{user_id}"),
                InlineKeyboardButton(text="Назад", callback_data=f"back_to_shop_{user_id}")
            ]
        ]
    )

    business_price = f"{business_price:,}".replace(",", ".")
    business_profit_hour = f"{business_profit_hour:,}".replace(",", ".")

    media_file = f"image/business_{business_id}.png"
    photo = FSInputFile(media_file, filename=os.path.basename(media_file))

    await bot.send_photo(chat_id=callback.message.chat.id, photo=photo,
                         caption=f"<u>{business_id}</u> - <b>{business_name}</b>\n"
                                 f"---------------------\n"
                                 f"Описание: <b>{business_desc}</b>\n"
                                 f"---------------------\n"
                                 f"Стоимость: <u>{business_price}</u> руб.\n"
                                 f"Прибыль: <u>{business_profit_hour}</u> руб/ч", reply_markup=inline_kb)


@shop_business.callback_query(F.data.startswith("buy_business_"))
async def callbacks_business_info_(callback: CallbackQuery):
    action = callback.data.split("_")
    business_id = action[2]
    user_id = action[3]

    cursor.execute(
        "SELECT * FROM business WHERE user_id = ? AND business_id = ?",
        (user_id, business_id,))
    result = cursor.fetchone()

    if result is not None:
        await callback.answer(show_alert=True, text="❌ У вас уже есть данный бизнес!")
        return

    print(result)

    cursor.execute(
        "SELECT business_name, business_price, business_profit_hour FROM business_info WHERE business_id = ?",
        (business_id,))
    result = cursor.fetchone()

    business_name, business_price, business_profit_hour = result

    cursor.execute("SELECT rubles, profit_hour FROM game WHERE user_id = ?", (callback.from_user.id,))
    result = cursor.fetchone()
    rubles, profit_hour = result

    profit_hour += business_profit_hour

    rubles_end = f"{rubles:,}".replace(",", ".")
    business_price_end = f"{business_price:,}".replace(",", ".")
    profit_hour_end = f"{profit_hour:,}".replace(",", ".")

    if rubles < business_price:
        await callback.answer(show_alert=True,
                              text=f"❌ К сожалению у вас недостаточно средств! ( {rubles_end} / {business_price_end} )")
        return

    cursor.execute("UPDATE game SET rubles = ?, profit_hour = ? WHERE user_id = ?",
                   (rubles - business_price, profit_hour, user_id,))
    conn.commit()

    now_time = int(time.time())

    db_table_business(callback.from_user.id, business_id, business_name, business_profit_hour, now_time)

    await bot.edit_message_caption(message_id=callback.message.message_id, chat_id=callback.message.chat.id,
                                   caption=f"✔ Вы успешно приобрели бизнес <b>{business_name}</b>, поздравляем! 🎉\n"
                                           f"Теперь ваша прибыль со всех бизнесов составляет: <u>{profit_hour_end}</u>₽/ч 💸\n\n"
                                           f"👤 Посмотреть бизнес можно по команде <u><b>/my_business</b></u>")
