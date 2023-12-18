import asyncio
import logging

from aiogram import Bot, Dispatcher

from Telequiz.config_data.config import load_config, Config
from Telequiz.keyboards.set_commands import set_main_commands
from Telequiz.handlers import menu_handlers, create_quiz_handlers


async def main():
    logging.basicConfig(level=logging.INFO)
    config: Config = load_config()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher()

    dp.include_router(create_quiz_handlers.rt)
    dp.include_router(menu_handlers.rt)

    await set_main_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
