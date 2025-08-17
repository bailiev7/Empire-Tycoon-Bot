from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
start = Router()  # [1]

@start.message(Command(commands="start"))  # [2]
async def cmd_start(message: Message):

    await message.reply("Добро пожаловать в тайкун «<b>Империя золота</b>» 🎉\n"
                        "Тут ты можешь прокачивать бизнесы, улучшать фермы и расширять свои территории!\n\n"
                        "Для начала игры пропиши /business и начинай богатеть! 🤑")


#F.text == "команда"