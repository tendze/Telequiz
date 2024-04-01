from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import factories
from math import ceil
from classes.question import Question
from lexicon.LEXICON_RU import LEXICON
from database.db_services import RecordTypes

edit_button_row = [InlineKeyboardButton(text=LEXICON['edit'], callback_data='edit')]
cancel_edit_button_row = [InlineKeyboardButton(text=LEXICON['cancel_edit'], callback_data='cancel_edit')]
new_question_button_row = [InlineKeyboardButton(text=LEXICON['new_question'], callback_data='new_question')]
delete_question_button_row = [InlineKeyboardButton(text=LEXICON['delete_question'], callback_data='delete_question')]
ready_button_row = [InlineKeyboardButton(text=LEXICON['ready'], callback_data='ready')]
cancel_button_row = [InlineKeyboardButton(text=LEXICON['cancel'], callback_data='cancel')]
back_button_row = [InlineKeyboardButton(text=LEXICON['go_back'], callback_data='go_back')]
run_quiz_row = [InlineKeyboardButton(text=LEXICON['run'], callback_data='run_quiz')]
disconnect_quiz_row = [InlineKeyboardButton(text=LEXICON['disconnect'], callback_data='disconnect_quiz')]
next_question_row = [InlineKeyboardButton(text=LEXICON['next_question'], callback_data='next_question')]
nickname_confirmation_with_username_rows = [[InlineKeyboardButton(text=LEXICON['use_my_name'],
                                                                  callback_data='use_my_name')],
                                            [InlineKeyboardButton(text=LEXICON['use_my_tag'],
                                                                  callback_data='use_my_tag')],
                                            cancel_button_row]
nickname_confirmation_without_username_rows = [[InlineKeyboardButton(text=LEXICON['use_my_name'],
                                                                     callback_data='use_my_name')],
                                               cancel_button_row]
line_button_row = [InlineKeyboardButton(text='―――――――――――', callback_data='just_line')]
finish_quiz_button_row = [InlineKeyboardButton(text=LEXICON['finish_quiz'], callback_data='finish_quiz')]
participant_answer_question_row = [InlineKeyboardButton(text=LEXICON['answer'], callback_data='answer_question')]
quiz_record_confirmation_row = [InlineKeyboardButton(text=LEXICON['start'], callback_data='start_quiz'),
                                InlineKeyboardButton(text=LEXICON['view'], callback_data='view_record'),
                                InlineKeyboardButton(text=LEXICON['delete'], callback_data='delete_record'),
                                InlineKeyboardButton(text=LEXICON['cancel'], callback_data='cancel'), ]
test_record_confirmation_row = [InlineKeyboardButton(text=LEXICON['send'], callback_data='send_test'),
                                InlineKeyboardButton(text=LEXICON['view'], callback_data='view_record'),
                                InlineKeyboardButton(text=LEXICON['delete'], callback_data='delete_record'),
                                InlineKeyboardButton(text=LEXICON['cancel'], callback_data='cancel'), ]
deadline_confirmation_row = [InlineKeyboardButton(text=LEXICON['yes'], callback_data='yes'),
                             InlineKeyboardButton(text=LEXICON['no'], callback_data='no')]
agree_test_passing_rows = [[InlineKeyboardButton(text=LEXICON['pass'], callback_data='pass_test')],
                           [InlineKeyboardButton(text=LEXICON['refuse'], callback_data='refuse')]]
time_limit_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=LEXICON['double_backward'], callback_data='double_backward'),
     InlineKeyboardButton(text=LEXICON['backward'], callback_data='backward'),
     InlineKeyboardButton(text='10 сек.', callback_data='timer'),
     InlineKeyboardButton(text=LEXICON['forward'], callback_data='forward'),
     InlineKeyboardButton(text=LEXICON['double_forward'], callback_data='double_forward')],
    [InlineKeyboardButton(text=LEXICON['ready'], callback_data='ready')]
])
backwards_button = InlineKeyboardButton(text=LEXICON['backward'], callback_data='backward')
forward_button = InlineKeyboardButton(text=LEXICON['forward'], callback_data='forward')


# Возвращает объект типа InlineKeyboardMarkup, представляющий из себя кнопки в меню создания квиза/теста
def create_question_view_inline_markup(
        question: Question = None,
        edit_mode: bool = False,
        edit_question_button_visible: bool = False,
        delete_question_button_visible: bool = False,
        current_question_index: int = None,
        all_question_count: int = None
) -> InlineKeyboardMarkup:
    result = []
    if question is not None:
        for i in range(len(question.variants)):
            variant_text = question.variants[i]
            result.append([InlineKeyboardButton(
                text=LEXICON['tick'] + variant_text if variant_text in question.right_variants else
                question.variants[i],
                callback_data=factories.variants.VariantsFactory(var_number=i + 1).pack())]
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
    result.append(cancel_button_row)
    return InlineKeyboardMarkup(inline_keyboard=result)


# Возвращает объект типа InlineKeyboardMarkup, представляющий из себя список созданных квизов/тестов
def create_list_of_q_or_t_markup(
        type_: RecordTypes,
        height: int = 5,
        page: int = 1,
        back_button_visible: bool = True,
        **kwargs
) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    if len(kwargs) == 0:
        keyboard.append(back_button_row)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    total_pages = ceil(len(kwargs) / height)
    first_index_of_page = (page - 1) * height if page <= total_pages else (page - 2) * height
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


# Функция для изменения кнопки записи на кнопку с подтверждением
def create_confirmation_button(
        inline_keyboard: InlineKeyboardMarkup,
        callback_data: str,
        type_: str
) -> InlineKeyboardMarkup:
    for i in range(len(inline_keyboard.inline_keyboard)):
        for j in range(len(inline_keyboard.inline_keyboard[i])):
            if inline_keyboard.inline_keyboard[i][j].callback_data == callback_data:
                inline_keyboard.inline_keyboard[i] = quiz_record_confirmation_row if type_ == 'Q' \
                    else test_record_confirmation_row
                break
    return inline_keyboard


def create_quiz_variants_buttons(
        question: Question,
) -> list[list[InlineKeyboardButton]]:
    variants = question.variants
    r_variants_len = len(question.right_variants)
    result = []
    for i in range(len(variants)):
        if r_variants_len > 1:
            row = InlineKeyboardButton(
                text=LEXICON['empty_tick'] + variants[i],
                callback_data=factories.variants.VariantsFactory(var_number=i + 1).pack()
            )
        else:
            row = InlineKeyboardButton(
                text=LEXICON['empty_radio'] + variants[i],
                callback_data=factories.variants.VariantsFactory(var_number=i + 1).pack()
            )
        result.append([row])
    return result


def create_ticked_quiz_variants_buttons(
        keyboard: InlineKeyboardMarkup,
        variant_ticked_number: int
) -> (bool, InlineKeyboardMarkup):
    buttons: list[list[InlineKeyboardButton]] = keyboard.inline_keyboard

    for i in range(len(buttons)):
        for j in range(len(buttons[i])):
            if buttons[i][j].callback_data == 'blocked_answer_question':
                return False, keyboard

    line_index = -1
    for i in range(len(buttons)):
        if buttons[i][0].callback_data == 'just_line':
            line_index = i
            break

    is_tick = buttons[0][0].text.startswith(LEXICON['tick']) or buttons[0][0].text.startswith(LEXICON['empty_tick'])
    if is_tick:
        var_text = buttons[variant_ticked_number-1][0].text
        buttons[variant_ticked_number-1][0].text = LEXICON['empty_tick']+var_text.lstrip(LEXICON['tick']) if var_text.startswith(LEXICON['tick'])\
            else LEXICON['tick']+var_text.lstrip(LEXICON['empty_tick'])
        keyboard.inline_keyboard = buttons
        return True, keyboard
    for i in range(line_index):
        if variant_ticked_number - 1 == i:
            buttons[i][0].text = LEXICON['radio'] + buttons[i][0].text.lstrip(LEXICON['radio']).lstrip(LEXICON['empty_radio'])
        else:
            buttons[i][0].text = LEXICON['empty_radio'] + buttons[i][0].text.lstrip(LEXICON['radio']).lstrip(LEXICON['empty_radio'])
    keyboard.inline_keyboard = buttons
    return True, keyboard


# Ищет в маркапе кнопку с искомым callback_data и заменяет текст этой кнопки
# И за одно сам callback_data если параметр new_cb_data не None
def create_new_markup_with_button_text(
        keyboard: InlineKeyboardMarkup,
        cb_data_to_find: str,
        new_button_text: str,
        new_cb_data: str = None
) -> InlineKeyboardMarkup:
    buttons = keyboard.inline_keyboard
    for i in range(len(buttons)):
        for j in range(len(buttons[i])):
            if buttons[i][j].callback_data == cb_data_to_find:
                buttons[i][j].text = new_button_text
                if new_cb_data is not None:
                    buttons[i][j].callback_data = new_cb_data
    keyboard.inline_keyboard = buttons
    return keyboard


# Находит все помеченные ответы и возвращает список индексов
def get_quiz_question_ticked_answers_indexes(
    keyboard: InlineKeyboardMarkup
) -> list[int]:
    buttons = keyboard.inline_keyboard
    result = []
    for i in range(len(buttons)):
        for j in range(len(buttons[i])):
            if buttons[i][j].callback_data == 'just_line':
                break
            if buttons[i][j].text.startswith(LEXICON['radio']):
                return [i]
            if buttons[i][j].text.startswith(LEXICON['tick']):
                result.append(i)
    return result