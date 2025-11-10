import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import sqlite3

conn = sqlite3.connect("database/database.db")
cursor = conn.cursor()

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token="8345303607:AAFojeQ2xhrEqAGCYMgBrsc5lV0fC3EPmBY",
          default=DefaultBotProperties(
              parse_mode=ParseMode.HTML))
