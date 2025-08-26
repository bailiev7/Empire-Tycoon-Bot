import asyncio
import time
from typing import Callable, Dict, Any, Awaitable, Optional

from aiogram import Dispatcher, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, User, CallbackQuery
from cachetools import TTLCache

from __init__ import *
from handlers.business import business
from handlers.farm import farm
from handlers.my_business import my_business
from handlers.well_dollar import well_dollar
from handlers.premium_sub import premium_sub
from handlers.up_business import up_business
from handlers.profile import profile
from handlers.registration import registration
from handlers.shop_business import shop_business
from handlers.start import start

from handlers.clans.clan_create import clan_create
from handlers.clans.my_clan import my_clan
from handlers.clans.clan_kb import clan_kb
from handlers.clans.clan_settings import clan_settings


# Middleware с rate_limit и проверкой регистрации + защитой кнопок
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

        cursor.execute("SELECT premium_until FROM game WHERE user_id = ?", (user.id,))
        result = cursor.fetchone()
        if result:
            premium_until = result[0]

            now = int(time.time())

            if premium_until < now and premium_until != 0:
                cursor.execute("UPDATE game SET premium_status = 'False', premium_until = '0' WHERE user_id = ?",
                               (user.id,))
                conn.commit()

                await bot.send_message(
                    reply_to_message_id=m.message_id,
                    chat_id=m.chat.id,
                    text="⌛ К сожалению, срок вашей <b><u>PREMIUM</u></b> подписки истёк.\n"
                         "Для продления подписки воспользуйтесь командой <u><b>/premium</b></u>"
                )

        # 🔒 Проверка user_id в callback_data
        if isinstance(m, CallbackQuery) and m.data:
            parts = m.data.split("_")
            for p in reversed(parts):  # идем с конца, т.к. id чаще всего в конце
                if p.isdigit():
                    target_id = int(p)
                    if target_id != user.id:
                        await m.answer("❌ Кнопка была адресована не вам.", show_alert=True)
                        return

                    break  # нашли число — проверили и хватит

        return await handler(m, data)

    @staticmethod
    async def is_registered(user_id: int) -> bool:
        cursor.execute("SELECT user_id FROM user WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None


# Запуск процесса поллинга новых апдейтов
async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start)
    dp.include_router(registration)
    dp.include_router(business)
    dp.include_router(well_dollar)
    dp.include_router(profile)
    dp.include_router(up_business)
    dp.include_router(premium_sub)
    dp.include_router(my_business)
    dp.include_router(shop_business)
    dp.include_router(farm)

    dp.include_router(my_clan)
    dp.include_router(clan_kb)
    dp.include_router(clan_settings)
    dp.include_router(clan_create)

    dp.message.outer_middleware(Middleware())
    dp.callback_query.outer_middleware(Middleware())

    await bot.send_message(1409698085, "Бот запущен ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
