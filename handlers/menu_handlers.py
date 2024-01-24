from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from keyboards.menu_keyboards import main_menu_markup, my_profile_markup, cancel_markup
from lexicon.LEXICON_RU import LEXICON
from states.states import CreateQuizOrTestFSM, MainMenuFSM
from services.inline_keyboard_services import create_list_of_q_or_t_markup
from services.keyboard_services import create_quiz_markup, create_test_markup
from database.db_services import Types, get_user_type_names

from math import ceil

rt = Router()

quiz_list_height = 5
test_list_height = 5


@rt.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text=LEXICON['greeting'])
    await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.message(Command(commands='menu'), StateFilter(default_state))
async def process_menu_command(message: Message):
    await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.message(Command(commands='about'), StateFilter(default_state))
async def process_info_command(message: Message):
    await message.answer(text=LEXICON['about_bot'])


@rt.callback_query(F.data == "my_profile", StateFilter(default_state))
async def process_profile_button_press(cb: CallbackQuery):
    await cb.message.edit_text(text=LEXICON['my_profile'], reply_markup=my_profile_markup)


@rt.callback_query(F.data == "back_main_menu", StateFilter(default_state))
async def process_back_press(cb: CallbackQuery):
    await cb.message.edit_text(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.callback_query(F.data == "create_quiz", StateFilter(default_state))
async def process_create_quiz_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(text='Выберите действие',
                            reply_markup=create_quiz_markup)
    await state.set_state(CreateQuizOrTestFSM.create_or_cancel_state)
    await state.update_data(type=Types.Quiz)
    await cb.answer()


@rt.callback_query(F.data == "create_test", StateFilter(default_state))
async def process_create_test_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(text='Выберите действие',
                            reply_markup=create_test_markup)
    await state.set_state(CreateQuizOrTestFSM.create_or_cancel_state)
    await state.update_data(type=Types.Test)
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
                       await get_user_type_names(user_id, Types.Quiz)}
    quiz_list_markup = create_list_of_q_or_t_markup(type_=Types.Quiz,
                                                    height=quiz_list_height,
                                                    back_button_visible=True,
                                                    **user_quiz_names)
    if len(user_quiz_names) == 0:
        await cb.message.edit_text(text="Вы еще ничего не создали", reply_markup=quiz_list_markup)
    else:
        await cb.message.edit_text(text="Ваши квизы📝", reply_markup=quiz_list_markup)
        await state.update_data(user_quiz_names=user_quiz_names)
        await state.update_data(current_page=1)
        await state.update_data(total_pages=ceil(len(user_quiz_names) / quiz_list_height))
    await state.set_state(MainMenuFSM.q_or_t_view)
    await cb.answer()


@rt.callback_query(F.data == "my_tests", StateFilter(default_state))
async def process_my_quizzes_press(cb: CallbackQuery, state: FSMContext):
    user_id: int = cb.from_user.id
    user_quiz_names = {str(record['record_id']): record['name'] for record in
                       await get_user_type_names(user_id, Types.Test)}
    quiz_list_markup = create_list_of_q_or_t_markup(type_=Types.Test,
                                                    height=quiz_list_height,
                                                    back_button_visible=True,
                                                    **user_quiz_names)
    if len(user_quiz_names) == 0:
        await cb.message.edit_text(text="Вы еще ничего не создали", reply_markup=quiz_list_markup)
    else:
        await cb.message.edit_text(text="Ваши квизы📝", reply_markup=quiz_list_markup)
        await state.update_data(user_quiz_names=user_quiz_names)
        await state.update_data(current_page=1)
        await state.update_data(total_pages=ceil(len(user_quiz_names) / quiz_list_height))
    await state.set_state(MainMenuFSM.q_or_t_view)
    await cb.answer()


@rt.callback_query(F.data == 'go_back', StateFilter(MainMenuFSM.q_or_t_view))
async def process_go_back_press(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(text=LEXICON['my_profile'], reply_markup=my_profile_markup)


@rt.callback_query(F.data == 'backward', StateFilter(MainMenuFSM.q_or_t_view))
async def process_backwards_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data['current_page']
    user_quiz_names = data['user_quiz_names']
    if current_page > 1:
        current_page -= 1
        quiz_list_markup = create_list_of_q_or_t_markup(type_=Types.Quiz,
                                                        height=quiz_list_height,
                                                        page=current_page,
                                                        back_button_visible=True,
                                                        **user_quiz_names)
        await cb.message.edit_reply_markup(reply_markup=quiz_list_markup)
        await state.update_data(current_page=current_page)
    await cb.answer()


@rt.callback_query(F.data == 'forward', StateFilter(MainMenuFSM.q_or_t_view))
async def process_forward_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data['current_page']
    user_quiz_names = data['user_quiz_names']
    total_pages = data['total_pages']
    if current_page < total_pages:
        current_page += 1
        quiz_list_markup = create_list_of_q_or_t_markup(type_=Types.Quiz,
                                                        height=quiz_list_height,
                                                        page=current_page,
                                                        back_button_visible=True,
                                                        **user_quiz_names)
        await cb.message.edit_reply_markup(reply_markup=quiz_list_markup)
        await state.update_data(current_page=current_page)
    await cb.answer()


@rt.callback_query(StateFilter(default_state))
async def process_other_buttons_press(cb: CallbackQuery, state: FSMContext):
    await cb.answer(text='Пока не реализовано :((')
