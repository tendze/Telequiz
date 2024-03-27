from aiogram.utils.deep_linking import create_start_link
from bot import bot


async def create_deep_link_by_code(
        code,
        encode: bool = False
    ):
    return await create_start_link(bot, str(code), encode=encode)
