from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter, CommandObject
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup

from keyboards.menu_keyboards import main_menu_markup, my_profile_markup
from lexicon.LEXICON_RU import LEXICON
from states.states import CreateQuizOrTestFSM, MainMenuFSM, QuizSessionFSM
from services.inline_keyboard_services import create_list_of_q_or_t_markup, cancel_button_row
from services.keyboard_services import create_quiz_markup, create_test_markup
from database.db_services import RecordTypes, get_user_record_names
from handlers.quiz_and_test_list_height_config import quiz_list_height
from handlers.quiz_waiting_room_handlers import process_deep_code_retrieval

from math import ceil

rt = Router()


# Обработка команды /start.
@rt.message(
    CommandStart(),
    StateFilter(default_state, MainMenuFSM.q_or_t_list_view, MainMenuFSM.q_or_t_view, MainMenuFSM.confirmation)
)
async def process_start_command(message: Message, state: FSMContext, command: CommandObject):
    await state.clear()
    quiz_code = command.args
    if quiz_code is not None:
        if not quiz_code.isdigit() or len(quiz_code) != 6:
            msg = await message.answer(text=LEXICON['incorrect_arg_code'])
            await state.update_data(last_message_id=msg.message_id)
        else:
            await state.set_state(QuizSessionFSM.code_retrieval)
            msg = await message.answer(text='Обработка кода...')
            await state.update_data(last_message_id=msg.message_id)
            await process_deep_code_retrieval(message, state, command)
    else:
        await message.answer(text=LEXICON['greeting'])
        msg = await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
        await state.update_data(last_message_id=msg.message_id)


# Обработка команды /menu
@rt.message(Command(commands='menu'), StateFilter(default_state))
async def process_menu_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


# Обработка команды /about
@rt.message(Command(commands='about'), StateFilter(default_state))
async def process_info_command(message: Message):
    await message.answer(text=LEXICON['about_bot'])


# Обработка нажатия на кнопку "Мой профиль"
@rt.callback_query(F.data == "my_profile", StateFilter(default_state))
async def process_profile_button_press(cb: CallbackQuery):
    await cb.message.edit_text(text=LEXICON['my_profile'], reply_markup=my_profile_markup)


# Обработка нажатия на кнопку "Назад"
@rt.callback_query(F.data == "back_main_menu", StateFilter(default_state))
async def process_back_press(cb: CallbackQuery):
    await cb.message.edit_text(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


# Обработка нажатия на кнопку "Ввести код сессии"
@rt.callback_query(F.data == 'find_session', StateFilter(default_state))
async def process_find_session_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    message = await cb.message.answer(text='Введите шестизначный код сессии',
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=[cancel_button_row]))
    await state.set_state(QuizSessionFSM.code_retrieval)
    await state.update_data(last_message_id=message.message_id)


# Обработка нажатия на кнопку "Отмена"
@rt.callback_query(F.data == 'cancel', StateFilter(QuizSessionFSM.code_retrieval))
async def process_cancel_code_retrieval_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.clear()


# Обработка нажатия на кнопку "Создать квиз"
@rt.callback_query(F.data == "create_quiz", StateFilter(default_state))
async def process_create_quiz_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(text='Выберите действие',
                            reply_markup=create_quiz_markup)
    await state.set_state(CreateQuizOrTestFSM.create_or_cancel_state)
    await state.update_data(type=RecordTypes.Quiz)
    await cb.message.delete()
    await cb.answer()


# Обработка нажатия на кнопку "Создать тест"
@rt.callback_query(F.data == "create_test", StateFilter(default_state))
async def process_create_test_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(text='Выберите действие',
                            reply_markup=create_test_markup)
    await state.set_state(CreateQuizOrTestFSM.create_or_cancel_state)
    await state.update_data(type=RecordTypes.Test)
    await cb.message.delete()
    await cb.answer()


@rt.message(F.text == LEXICON['cancel'], StateFilter(CreateQuizOrTestFSM.create_or_cancel_state))
async def cancel_button_press(message: Message, state: FSMContext):
    await message.answer(text="Создание отменено", reply_markup=ReplyKeyboardRemove())
    await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.clear()


@rt.callback_query(F.data == "my_quizzes", StateFilter(default_state))
async def process_my_quizzes_press(cb: CallbackQuery, state: FSMContext):
    user_id: int = cb.from_user.id
    user_quiz_names = {str(record['record_id']): record['name'] for record in
                       await get_user_record_names(user_id, RecordTypes.Quiz)}
    quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz,
                                                    height=quiz_list_height,
                                                    back_button_visible=True,
                                                    **user_quiz_names)
    if len(user_quiz_names) == 0:
        await cb.message.edit_text(text="Вы еще ничего не создали", reply_markup=quiz_list_markup)
    else:
        await cb.message.edit_text(text=LEXICON['your_quizzes'], reply_markup=quiz_list_markup)
        await state.update_data(user_record_names=user_quiz_names)
        await state.update_data(current_list_page=1)
        await state.update_data(total_pages=ceil(len(user_quiz_names) / quiz_list_height))
    await state.set_state(MainMenuFSM.q_or_t_list_view)
    await cb.answer()


@rt.callback_query(F.data == "my_tests", StateFilter(default_state))
async def process_my_quizzes_press(cb: CallbackQuery, state: FSMContext):
    user_id: int = cb.from_user.id
    user_quiz_names = {str(record['record_id']): record['name'] for record in
                       await get_user_record_names(user_id, RecordTypes.Test)}
    quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Test,
                                                    height=quiz_list_height,
                                                    back_button_visible=True,
                                                    **user_quiz_names)
    if len(user_quiz_names) == 0:
        await cb.message.edit_text(text="Вы еще ничего не создали", reply_markup=quiz_list_markup)
    else:
        await cb.message.edit_text(text=LEXICON['your_tests'], reply_markup=quiz_list_markup)
        await state.update_data(user_record_names=user_quiz_names)
        await state.update_data(current_list_page=1)
        await state.update_data(total_pages=ceil(len(user_quiz_names) / quiz_list_height))
    await state.set_state(MainMenuFSM.q_or_t_list_view)
    await cb.answer()


# Обработка нажатия на остальные кнопки
@rt.callback_query(StateFilter(default_state))
async def process_other_buttons_press(cb: CallbackQuery, state: FSMContext):
    await cb.answer(text='Пока не реализовано :((')
