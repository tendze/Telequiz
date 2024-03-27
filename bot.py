from aiogram import Bot
from config_data.config import load_config, Config

config: Config = load_config()
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
