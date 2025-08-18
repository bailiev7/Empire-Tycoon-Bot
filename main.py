import asyncio
import logging
from typing import MutableMapping, Callable, Dict, Any, Awaitable, Optional

from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, User
from cachetools import TTLCache

from __init__ import *

from handlers.start import start
from handlers.business import business
from handlers.farm import farm
from handlers.shop_business import shop_business
from handlers.registration import registration


# Middleware с rate_limit и проверкой регистрации
class Middleware(BaseMiddleware):
    RATE_LIMIT = 1.0  # секунды

    def __init__(self, rate_limit: float = RATE_LIMIT) -> None:
        super().__init__()
        self.rate_limit = rate_limit
        self.cache: TTLCache[int, None] = TTLCache(maxsize=10000, ttl=rate_limit)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        m: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: Optional[User] = getattr(m, "from_user", None)
        state: FSMContext = data.get("state")

        if user is not None:
            # Rate limit
            if user.id in self.cache:
                return  # Блокируем, если слишком часто
            self.cache[user.id] = None

        # Проверка регистрации
        current_state = await state.get_state() if state else None
        is_registered = await self.is_registered(user.id) if user else True

        if not is_registered and current_state is None:
            if hasattr(m, "text") and m.text not in ["/рег", "/регистрация", "/registration", "/reg"]:
                await m.reply("Вы не зарегистрировались в системе\nЗарегистрируйтесь по команде: /registration")
                return

        return await handler(m, data)

    async def is_registered(self, user_id: int) -> bool:
        cursor.execute("SELECT user_id FROM user WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None


# Запуск процесса поллинга новых апдейтов
async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start)
    dp.include_router(registration)
    dp.include_router(business)
    dp.include_router(shop_business)
    dp.include_router(farm)
    # dp.include_router(profile)

    dp.message.outer_middleware(Middleware())

    await bot.send_message(1409698085, "Бот запущен ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())