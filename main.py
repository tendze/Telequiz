import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis

from config_data.config import load_config, Config
from keyboards.set_commands import set_main_commands
from handlers import menu_handlers, create_quiz_handlers
from database.db_services import initialize_db


async def main():
    logging.basicConfig(level=logging.INFO)
    config: Config = load_config()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher()

    dp.include_router(create_quiz_handlers.rt)
    dp.include_router(menu_handlers.rt)

    await initialize_db()
    await set_main_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
