from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Telequiz.types.question import Question
from Telequiz.factories.variants import VariantsFactory
from Telequiz.lexicon.LEXICON_RU import LEXICON

edit_button_row = [InlineKeyboardButton(text=LEXICON['edit'], callback_data='edit')]
cancel_edit_button_row = [InlineKeyboardButton(text=LEXICON['cancel_edit'], callback_data='cancel_edit')]
new_question_button_row = [InlineKeyboardButton(text=LEXICON['new_question'], callback_data='new_question')]
delete_question_button_row = [InlineKeyboardButton(text=LEXICON['delete_question'], callback_data='delete_question')]
ready_button_row = [InlineKeyboardButton(text=LEXICON['ready'], callback_data='ready')]
cancel_button_row = [InlineKeyboardButton(text=LEXICON['cancel'], callback_data='cancel')]


def create_constructor_inline_markup(question: Question = None,
                                     edit_mode: bool = False,
                                     delete_question_button_visible: bool = False,
                                     current_question_index: int = None,
                                     all_question_count: int = None) -> InlineKeyboardMarkup:
    result = []
    if question is not None:
        for i in range(len(question.variants)):
            result.append([InlineKeyboardButton(
                text=LEXICON['cross_emoji'] + question.variants[i].lstrip(LEXICON['tick']) if edit_mode else question.variants[i],
                callback_data=VariantsFactory(var_number=i).pack())]
            )
        result.append(
            [InlineKeyboardButton(text=LEXICON['backward'], callback_data='backward'),
             InlineKeyboardButton(text=f'{current_question_index}/{all_question_count}', callback_data='question_index'),
             InlineKeyboardButton(text=LEXICON['forward'], callback_data='forward')]
        )
    if not edit_mode:
        result.append(edit_button_row)
    else:
        result.append(cancel_edit_button_row)
    result.append(new_question_button_row)
    if delete_question_button_visible:
        result.append(delete_question_button_row)
    result.append(ready_button_row)
    result.append(cancel_button_row)
    return InlineKeyboardMarkup(inline_keyboard=result)


def create_selected_button_markup(markup: InlineKeyboardMarkup, *selected_button_data: str) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    for i in range(len(keyboard)):
        for j in range(len(keyboard[i])):
            if keyboard[i][j].callback_data in selected_button_data:
                button_text = keyboard[i][j].text
                keyboard[i][j].text = button_text.lstrip(LEXICON['tick']) if button_text.startswith(LEXICON['tick'])\
                    else LEXICON['tick'] + button_text
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def is_any_button_checked(markup: InlineKeyboardMarkup) -> tuple[list[str], bool]:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    keyboard.pop()
    flag: bool = False
    right_answers: list[str] = []
    for row in keyboard:
        for button in row:
            if button.text.startswith("✓ "):
                flag = True
                right_answers.append(button.text.lstrip('✓ '))
    return right_answers, flag


def clean_variants_markup(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    for i in range(len(keyboard)):
        for j in range(len(keyboard[i])):
            if keyboard[i][j].text.startswith('✓ '):
                keyboard[i][j].text = keyboard[i][j].text.lstrip('✓ ')
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def is_checked_variants_right(markup: InlineKeyboardMarkup, right_answers: list[str]) -> bool:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    right_answer_checked_count: int = 0
    for row in keyboard:
        for button in row:
            text = button.text.lstrip("✓ ")
            if button.text != text and text in right_answers:
                right_answer_checked_count += 1
    if right_answer_checked_count != len(right_answers):
        return False
    return True
