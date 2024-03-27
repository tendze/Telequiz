import asyncio
import logging

from aiogram import Dispatcher

from keyboards.set_commands import set_main_commands
from handlers import menu_handlers, create_quiz_and_test_handlers, quiz_and_test_view_handlers
from database.db_services import initialize_db
from bot import bot


async def main():
    logging.basicConfig(level=logging.INFO)
    dp = Dispatcher()
    dp.include_router(menu_handlers.rt)
    dp.include_router(create_quiz_and_test_handlers.rt)
    dp.include_router(quiz_and_test_view_handlers.rt)

    await initialize_db()
    await set_main_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
