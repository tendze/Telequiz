from Telequiz.lexicon.LEXICON_RU import LEXICON

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


__main_menu_buttons: list[list[InlineKeyboardButton]] = [
    [InlineKeyboardButton(text=LEXICON['find_session'], callback_data="find_session")],
    [
        InlineKeyboardButton(text=LEXICON['create_quiz'], callback_data="create_quiz"),
        InlineKeyboardButton(text=LEXICON['create_test'], callback_data="create_test")
    ],
    [InlineKeyboardButton(text=LEXICON['my_profile'], callback_data="my_profile")],
]
main_menu_markup = InlineKeyboardMarkup(
    inline_keyboard=__main_menu_buttons
)

__my_profile_buttons: list[list[InlineKeyboardButton]] = [
    [InlineKeyboardButton(text=LEXICON['my_quizzes'], callback_data="my_quizzes")],
    [InlineKeyboardButton(text=LEXICON['my_tests'], callback_data="my_tests")],
    [InlineKeyboardButton(text=LEXICON['statistics'], callback_data="statistics")],
    [InlineKeyboardButton(text=LEXICON['go_back'], callback_data="back_main_menu")]
]
my_profile_markup = InlineKeyboardMarkup(
    inline_keyboard=__my_profile_buttons
)

__cancel_button: list[list[InlineKeyboardButton]] = [
    [InlineKeyboardButton(text=LEXICON['cancel'], callback_data='cancel')]
]
cancel_markup = InlineKeyboardMarkup(
    inline_keyboard=__cancel_button
)