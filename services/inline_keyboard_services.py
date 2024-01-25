from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import factories
from math import ceil
from classes.question import Question
from lexicon.LEXICON_RU import LEXICON
from database.db_services import Types

edit_button_row = [InlineKeyboardButton(text=LEXICON['edit'], callback_data='edit')]
cancel_edit_button_row = [InlineKeyboardButton(text=LEXICON['cancel_edit'], callback_data='cancel_edit')]
new_question_button_row = [InlineKeyboardButton(text=LEXICON['new_question'], callback_data='new_question')]
delete_question_button_row = [InlineKeyboardButton(text=LEXICON['delete_question'], callback_data='delete_question')]
ready_button_row = [InlineKeyboardButton(text=LEXICON['ready'], callback_data='ready')]
cancel_button_row = [InlineKeyboardButton(text=LEXICON['cancel'], callback_data='cancel')]
back_button_row = [InlineKeyboardButton(text=LEXICON['go_back'], callback_data='go_back')]
backwards_button = InlineKeyboardButton(text=LEXICON['backward'], callback_data='backward')
forward_button = InlineKeyboardButton(text=LEXICON['forward'], callback_data='forward')
time_limit_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=LEXICON['double_backward'], callback_data='double_backward'),
     InlineKeyboardButton(text=LEXICON['backward'], callback_data='backward'),
     InlineKeyboardButton(text='10 сек.', callback_data='timer'),
     InlineKeyboardButton(text=LEXICON['forward'], callback_data='forward'),
     InlineKeyboardButton(text=LEXICON['double_forward'], callback_data='double_forward')],
    [InlineKeyboardButton(text=LEXICON['ready'], callback_data='ready')]
])


# Возвращает объект типа InlineKeyboardMarkup, представляющий из себя кнопки в меню создания квиза/теста
def create_constructor_inline_markup(question: Question = None,
                                     edit_mode: bool = False,
                                     edit_question_button_visible: bool = False,
                                     delete_question_button_visible: bool = False,
                                     ready_button_visible: bool = True,
                                     current_question_index: int = None,
                                     all_question_count: int = None) -> InlineKeyboardMarkup:
    result = []
    if question is not None:
        for i in range(len(question.variants)):
            result.append([InlineKeyboardButton(
                text=LEXICON['cross_emoji'] + question.variants[i].lstrip(LEXICON['tick']) if edit_mode else
                question.variants[i],
                callback_data=factories.variants.VariantsFactory(var_number=i).pack())]
            )
        result.append(
            [backwards_button,
             InlineKeyboardButton(text=f'{current_question_index}/{all_question_count}',
                                  callback_data='question_index'),
             forward_button]
        )
    if not edit_mode and edit_question_button_visible:
        result.append(edit_button_row)
    elif edit_mode:
        result.append(cancel_edit_button_row)
    result.append(new_question_button_row)
    if delete_question_button_visible:
        result.append(delete_question_button_row)
    if ready_button_visible:
        result.append(ready_button_row)
    result.append(cancel_button_row)
    return InlineKeyboardMarkup(inline_keyboard=result)


# Возвращает объект типа InlineKeyboardMarkup, представляющий из себя список созданных квизов/тестов
def create_list_of_q_or_t_markup(type_: Types,
                                 height: int = 5,
                                 page: int = 1,
                                 back_button_visible: bool = True,
                                 **kwargs) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    total_pages = ceil(len(kwargs) / height)
    first_index_of_page = (page - 1) * height
    kwargs_list = [x for x in kwargs.items()]
    for i in range(first_index_of_page, min(first_index_of_page + height, len(kwargs))):
        keyboard.append([InlineKeyboardButton(text=kwargs_list[i][1],
                                              callback_data=factories.user_records.UserRecordsFactory(
                                                  record_id=kwargs_list[i][0],
                                                  type_=type_.value).pack())])

    if len(kwargs) > height:
        keyboard.append([backwards_button,
                         InlineKeyboardButton(text=f'{page if page < total_pages else total_pages}/{total_pages}',
                                              callback_data='question_index'),
                         forward_button])
    if back_button_visible:
        keyboard.append(back_button_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_confirmation_button(inline_keyboard: InlineKeyboardMarkup,
                               record_id: int) -> InlineKeyboardMarkup:
    pass
