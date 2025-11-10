import json

import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from __init__ import *

well_dollar = Router()


@well_dollar.callback_query(F.data.startswith("dollars"))
@well_dollar.message(Command(commands="dollars"))
@well_dollar.message(F.text.casefold() == "доллары")
async def cmd_well_dollars(message: Message | CallbackQuery):
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                data = json.loads(text)

                usd = data["Valute"]["USD"]["Value"]
                prev = data["Valute"]["USD"]["Previous"]

                diff = usd - prev
                percent = (diff / prev) * 100 if prev != 0 else 0

                if diff > 0:
                    emodz = "🟢"
                    trend = f"📈 (+{percent:.2f}%)"
                elif diff < 0:
                    emodz = "🔴"
                    trend = f"📉 ({percent:.2f}%)"
                else:
                    trend = "⚪️➖ (0.00%)"

                inline_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="Купить доллары 💲",
                                                 callback_data=f"chech_dollars_{message.from_user.id}"),
                            InlineKeyboardButton(text="Продать доллары 💹",
                                                 callback_data=f"sell_dollars_{message.from_user.id}")
                        ]
                    ]
                )

                cursor.execute("SELECT tutorial FROM game WHERE user_id = ?", (message.from_user.id,))
                result = cursor.fetchone()

                tutorial = result[0]

                if tutorial == 6:
                    cursor.execute("UPDATE game SET tutorial = '7' WHERE user_id = ?", (message.from_user.id,))
                    conn.commit()

                    text = (f"💵 Курс доллара ЦБ РФ:\n\n"
                            f"{emodz} 1 USD = {usd:.2f} ₽ {trend}\n"
                            f"(вчера было {prev:.2f} ₽)\n\n"
                            f"📜 Тут ты можешь посмотреть актуальный курс доллара центробанка и обменять рубли на доллары согласно курсу, но с небольшой комиссией\n\n"
                            f"Следующим шагом будет статистика. Вееди <u><b>/top</b></u>")

                else:
                    text = (f"💵 Курс доллара ЦБ РФ:\n\n"
                            f"{emodz} 1 USD = {usd:.2f} ₽ {trend}\n"
                            f"(вчера было {prev:.2f} ₽)")

                if isinstance(message, Message):
                    await message.reply(
                        text=text,
                        reply_markup=inline_kb
                    )

                else:
                    await bot.edit_message_text(
                        message_id=message.message.message_id,
                        chat_id=message.message.chat.id,
                        text=text,
                        reply_markup=inline_kb
                    )

    except Exception as e:
        await message.answer("❌ Не удалось получить курс доллара. Попробуй позже.")
        print(f"[ERROR] {e}")


@well_dollar.callback_query(F.data.startswith("chech_dollars_"))
async def cmd_check_dollars(message: Message | CallbackQuery):
    price_list = []

    if isinstance(message, Message):
        user_id = message.from_user.id

    else:
        split = message.data.split("_", 2)
        user_id = split[2]

    cursor.execute("SELECT rubles FROM game WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    rubles = result[0]

    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                data = json.loads(text)

                usd = data["Valute"]["USD"]["Value"]

                one_dollars = round(usd, 1)
                ten_dollars = round(usd * 10 * 1.05, 1)
                one_hundred_dollars = round(usd * 100 * 1.05, 1)
                thousand_dollars = round(usd * 1000 * 1.05, 1)
                ten_thousand_dollars = round(usd * 10000 * 1.05, 1)

                price_list.append(f"💵 Обмен валют:\n")

                price_list.append(f"━━━━━━━━━━━━━━━\n")
                price_list.append(f"1$ - {one_dollars:,} руб\n")
                price_list.append(f"10$ - {ten_dollars:,} руб\n")
                price_list.append(f"100$ - {one_hundred_dollars:,} руб\n")
                price_list.append(f"1.000$ - {thousand_dollars:,} руб\n")
                price_list.append(f"10.000$ - {ten_thousand_dollars:,} руб\n")
                price_list.append(f"(Цены указаны с учетом <b>комиссии 5%</b>)\n")
                price_list.append(f"━━━━━━━━━━━━━━━\n")

                price_list.append(f"Ваш баланс составляет: {rubles:,} руб")

                price_list = "".join(price_list)

                usd_with_fee = usd * 1.05
                select = int(rubles // usd_with_fee)

                inline_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="1$", callback_data=f"buy_dollars_1_{message.from_user.id}"),
                            InlineKeyboardButton(text="10$", callback_data=f"buy_dollars_10_{message.from_user.id}"),
                            InlineKeyboardButton(text="100$", callback_data=f"buy_dollars_100_{message.from_user.id}")
                        ],
                        [
                            InlineKeyboardButton(text="1,000$",
                                                 callback_data=f"buy_dollars_1000_{message.from_user.id}"),
                            InlineKeyboardButton(text="10,000$",
                                                 callback_data=f"buy_dollars_10000_{message.from_user.id}"),
                            InlineKeyboardButton(text=f"{select:,}$",
                                                 callback_data=f"buy_dollars_{select}_{message.from_user.id}"),
                        ],
                        [
                            #InlineKeyboardButton(text="Своя сумма",
                             #                    callback_data=f"buy_select_dollars_{message.from_user.id}"),
                            InlineKeyboardButton(text="◀ Назад",
                                                 callback_data=f"dollars_{message.from_user.id}")
                        ]
                    ]
                )

                await bot.edit_message_text(
                    chat_id=message.message.chat.id,
                    message_id=message.message.message_id,
                    text=price_list,
                    reply_markup=inline_kb
                )

    except Exception as e:
        await message.answer("❌ Не удалось получить курс доллара. Попробуйте позже.")
        print(f"[ERROR] {e}")


@well_dollar.callback_query(F.data.startswith("buy_dollars_"))
async def cmd_buy_dollars(message: Message | CallbackQuery):
    action = message.data.split("_")
    count = int(action[2])
    user_id = action[3]

    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                data = json.loads(text)

                usd = data["Valute"]["USD"]["Value"]

                usd_with_fee = usd * 1.05
                price = round(count * usd_with_fee, 1)

                cursor.execute("SELECT rubles, dollars FROM game WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                rubles, dollars = result

                if rubles < price:
                    await message.answer(f"❌ У вас недостаточно средств ({rubles:,}/{price:,}")
                    return

                rubles -= round(price)
                dollars += count

                cursor.execute("UPDATE game SET rubles = ?, dollars = ? WHERE user_id = ?", (rubles, dollars, user_id,))
                conn.commit()

                await bot.send_message(
                    chat_id=message.message.chat.id,
                    text=f"✔ Вы успешно купили {count}$ за {price:,}₽\n"
                         f"Баланс рублей: {rubles:,}₽\n"
                         f"Баланс долларов: {dollars:,}$"
                )

    except Exception as e:
        await message.answer("❌ Не удалось получить курс доллара. Попробуйте позже.")
        print(f"[ERROR] {e}")


@well_dollar.callback_query(F.data.startswith("sell_dollars_"))
async def cmd_sell_dollars(callback: CallbackQuery):
    action = callback.data.split("_")
    user_id = action[2]

    cursor.execute("SELECT rubles, dollars FROM game WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    rubles, dollars = result

    if dollars <= 0:
        await callback.answer("❌ У вас нет долларов для продажи!", show_alert=True)
        return

    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                data = json.loads(text)

                usd = data["Valute"]["USD"]["Value"]
                usd_with_fee = usd * 0.95  # курс с комиссией при продаже

                # считаем цены
                one_dollars = round(usd_with_fee * 1, 1)
                ten_dollars = round(usd_with_fee * 10, 1)
                one_hundred_dollars = round(usd_with_fee * 100, 1)
                thousand_dollars = round(usd_with_fee * 1000, 1)
                ten_thousand_dollars = round(usd_with_fee * 10000, 1)

                # формируем текст
                price_list = ["💵 Продажа валют:\n",
                              "━━━━━━━━━━━━━━━\n",
                              f"1$ - {one_dollars:,} руб\n",
                              f"10$ - {ten_dollars:,} руб\n",
                              f"100$ - {one_hundred_dollars:,} руб\n",
                              f"1,000$ - {thousand_dollars:,} руб\n",
                              f"10,000$ - {ten_thousand_dollars:,} руб\n",
                              "(Цены указаны с учетом <b>комиссии 5%</b>)\n",
                              "━━━━━━━━━━━━━━━\n",
                              f"Ваш баланс:\n"
                              f"Рубли: {rubles:,}₽\n"
                              f"Доллары: {dollars:,}$"]

                text_msg = "".join(price_list)

                # клавиатура
                sell_keyboard = [
                    [
                        InlineKeyboardButton(text="1$", callback_data=f"sell_do_1_{user_id}"),
                        InlineKeyboardButton(text="10$", callback_data=f"sell_do_10_{user_id}"),
                        InlineKeyboardButton(text="100$", callback_data=f"sell_do_100_{user_id}")
                    ],
                    [
                        InlineKeyboardButton(text="1,000$", callback_data=f"sell_do_1000_{user_id}"),
                        InlineKeyboardButton(text="10,000$", callback_data=f"sell_do_10000_{user_id}"),
                        InlineKeyboardButton(text=f"Все ({dollars:,}$)", callback_data=f"sell_do_{dollars}_{user_id}")
                    ]
                ]

                await callback.message.edit_text(
                    text=text_msg,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=sell_keyboard)
                )

    except Exception as e:
        await callback.answer("❌ Не удалось получить курс доллара. Попробуйте позже.", show_alert=True)
        print(f"[ERROR] {e}")


@well_dollar.callback_query(F.data.startswith("sell_do_"))
async def cmd_do_sell_dollars(callback: CallbackQuery):
    action = callback.data.split("_")
    count = int(action[2])
    user_id = action[3]

    cursor.execute("SELECT rubles, dollars FROM game WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    rubles, dollars = result

    if count > dollars:
        await callback.answer("❌ У вас недостаточно долларов для продажи!", show_alert=True)
        return

    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                data = json.loads(text)

                usd = data["Valute"]["USD"]["Value"]
                usd_with_fee = usd * 0.95  # курс продажи с комиссией
                price = round(count * usd_with_fee, 1)

                dollars -= count
                rubles += round(price)

                cursor.execute("UPDATE game SET rubles = ?, dollars = ? WHERE user_id = ?", (rubles, dollars, user_id))
                conn.commit()

                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f"✔️ Вы успешно продали {count:,}$ за {price:,}₽\n"
                         f"Баланс рублей: {rubles:,}₽\n"
                         f"Баланс долларов: {dollars:,}$"
                )

    except Exception as e:
        await callback.answer("❌ Не удалось получить курс доллара. Попробуйте позже.", show_alert=True)
        print(f"[ERROR] {e}")
