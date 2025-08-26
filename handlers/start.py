from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message

from __init__ import *

start = Router()  # [1]


@start.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandObject):
    payload = command.args  # сюда прилетает всё, что после ?start=

    if not payload:
        return  # на всякий случай, если вдруг пусто

    if payload.startswith("clan_"):
        try:
            _, clan_id, _, inviter_id = payload.split("_")
            clan_id = int(clan_id)
            inviter_id = int(inviter_id)

            cursor.execute("SELECT profit_hour, clan_id FROM game WHERE user_id = ?", (message.from_user.id,))
            profit_hour, clan_id_user = cursor.fetchone()

            if profit_hour < 100000:
                await message.reply("❌ К сожалению у вас недостаточно прибыли в час для вступления в кланы")
                return

            if clan_id_user != 0:
                if clan_id == clan_id_user:
                    await message.reply("❌ Вы уже состоите в этом клане!")
                    return

                await message.reply("❌ Вы уже состоите в клане!")
                return

            cursor.execute("SELECT clan_name, clan_invite_status FROM clans WHERE clan_id = ?", (clan_id,))
            clan_name, clan_invite_status = cursor.fetchone()

            if clan_invite_status == "False":
                await message.reply("❌ Приглашения в клан было закрыто создателем клана!")
                return

            cursor.execute("SELECT name_bot FROM user WHERE user_id = ?", (inviter_id,))
            name_bot = cursor.fetchone()[0]

            cursor.execute("UPDATE game SET clan_id = ?, clan_status = ? WHERE user_id = ?", (clan_id, "участник ⭐", message.from_user.id,))
            conn.commit()

            # тут можешь сразу добавить игрока в клан в базе
            await message.answer(
                f"👋 Привет! Ты успешно присоединился к клану «<b><u>{clan_name}</u></b>».\n"
                f"Приглашение отправлено от пользователя <a href='tg://user?id={inviter_id}'>{name_bot}</a>!"
            )

        except:
            await message.answer("❌ Ошибка при обработке ссылки. Попробуй ещё раз.")
    else:
        await message.answer(f"Ты пришёл по ссылке с параметром: {payload}")


@start.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "Добро пожаловать в тайкун «<b>Империя золота</b>» 🎉\n"
        "Тут ты можешь прокачивать бизнесы, улучшать фермы и расширять свои территории!\n\n"
        "Для начала игры пропиши /business и начинай богатеть! 🤑"
    )

# Exception as e
