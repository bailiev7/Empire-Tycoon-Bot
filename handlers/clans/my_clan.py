from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message

from __init__ import *  # подключение к БД

my_clan = Router()


@my_clan.message(F.text.casefold() == "мой клан")
@my_clan.message(Command(commands="my_clan"))
async def cmd_clan_create(message: Message):
    cursor.execute("SELECT clan_id, clan_status FROM game WHERE user_id = ?", (message.from_user.id,))

    clan_id, clan_status = cursor.fetchone()

    if clan_id == 0:
        await message.reply("❌ Вы не состоите в клане!")
        return

    cursor.execute("SELECT * FROM clans WHERE clan_id = ?", (clan_id,))
    clan_id, owner_id, clan_name, clan_desc, clan_rating, clan_safe, clan_safe_status, clan_list_status, clan_invite_status = cursor.fetchone()

    cursor.execute("SELECT user_id FROM game WHERE clan_id = ?", (clan_id,))
    members = cursor.fetchall()

    text_message = [f"📜 Название клана: <b><u>{clan_name}</u></b> ({clan_id})",
                    f"⭐ Рейтинг клана: <u>{clan_rating}</u>",
                    f"👥 Участников: <u>{len(members):,}</u>",
                    f"🌟 Ваш статус: <b>{clan_status}</b>"]

    if clan_safe_status == "False":
        clan_safe_status = "скрыт 🚫"

    else:
        clan_safe_status = f"{clan_safe:,}₽"

    text_message.append(
        f"🏛 Сейф клана: {clan_safe_status}"
    )

    if clan_desc is None:
        text_message.append(
            f"\n━━━━━━━━━━━━━━━\n"
            f"Описание клана:\n"
            f"<b>{clan_desc}</b>\n"
            f"━━━━━━━━━━━━━━━"
        )

    else:
        None

    text_message = "\n".join(text_message)

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Список участников",
                                     callback_data=f"clan_list_{message.from_user.id}"),
                InlineKeyboardButton(text="🏅 Достижения клана",
                                     callback_data=f"clan_achievments_{message.from_user.id}"),
                InlineKeyboardButton(text="💰 Сейф клана",
                                     callback_data=f"clan_safe_{message.from_user.id}")
            ],
            [
                InlineKeyboardButton(text="🤝 Союзы клана",
                                     callback_data=f"clan_union_{message.from_user.id}"),
                InlineKeyboardButton(text="➕ Пригласить участника",
                                     callback_data=f"clan_add_friend_{message.from_user.id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Покинуть клан",
                                     callback_data=f"clan_leave_{message.from_user.id}"),
                InlineKeyboardButton(text="⚙ Настройки клана",
                                     callback_data=f"clan_settings_{message.from_user.id}")
            ]
        ]
    )

    await message.reply(text_message, reply_markup=inline_kb)
