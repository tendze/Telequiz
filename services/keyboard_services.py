from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from lexicon.LEXICON_RU import LEXICON

create_quiz_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=LEXICON["create_quiz"],
                                                                   web_app=WebAppInfo(url='https://tendze.github.io/'))],
                                                   [KeyboardButton(text=LEXICON["cancel"])]],
                                         resize_keyboard=True,
                                         input_field_placeholder="Выберите действие")
create_test_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=LEXICON["create_test"],
                                                                   web_app=WebAppInfo(url='https://tendze.github.io/'))],
                                                   [KeyboardButton(text=LEXICON["cancel"])]],
                                         resize_keyboard=True,
                                         input_field_placeholder="Выберите действие")
