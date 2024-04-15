import asyncio
import logging

from keyboards.set_commands import set_main_commands
from handlers import (
    menu_handlers,
    create_quiz_and_test_handlers,
    quiz_and_test_view_handlers,
    quiz_waiting_room_handlers,
    quiz_passing_handlers,
    test_passing_handlers
)
from aiogram_dialog import setup_dialogs
from database.db_services import initialize_db
from bot import bot
from dispatcher import dp


async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_routers(
        menu_handlers.rt,
        create_quiz_and_test_handlers.rt,
        quiz_and_test_view_handlers.rt,
        quiz_waiting_room_handlers.rt,
        quiz_passing_handlers.rt,
        test_passing_handlers.rt,
    )
    setup_dialogs(dp)

    await initialize_db()
    await set_main_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
