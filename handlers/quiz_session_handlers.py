from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, CommandStart, CommandObject
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from database.db_services import *
from services.inline_keyboard_services import *
from states.states import *
from handlers.quiz_and_test_list_height_config import quiz_list_height
from lexicon.LEXICON_RU import LEXICON
from keyboards.menu_keyboards import main_menu_markup
from bot import bot

rt = Router()


@rt.message(StateFilter(QuizSessionFSM.code_retrieval))
async def process_code_retrieval(message: Message, state: FSMContext):
    last_message_id = (await state.get_data())['last_message_id']
    code = message.text
    if not code.isdigit() or len(code) != 6:
        await bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
        message = await message.answer(text=LEXICON['incorrect_code'],
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[cancel_button_row]))
        await state.update_data(last_message_id=message.message_id)
        return
    quiz_session_info = await get_quiz_session_info_by_code(code)
    if quiz_session_info is None:
        await bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
        message = await message.answer(text=LEXICON['code_doesnt_exists'],
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[cancel_button_row]))
        await state.update_data(last_message_id=message.message_id)
    else:
        quiz_name = await get_user_record_info_by_id(quiz_session_info['quiz_record_id'])
        await message.answer(text=f'Сессия найдена:\n'
                                  f'<b>{quiz_name["name"]}</b>')
        which_inline_keyboard = nickname_confirmation_with_username_rows if message.from_user.username is not None else nickname_confirmation_without_username_rows
        await message.answer(
            text='Введите свой собственный никнейм, не превышающий <u>30 символов</u>.',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=which_inline_keyboard
            )
        )
        await state.set_state(QuizSessionFSM.nickname_retrieval)


@rt.message(StateFilter(QuizSessionFSM.nickname_retrieval))
async def process_name_input(message: Message, state: FSMContext):
    pass


@rt.callback_query(F.data == 'cancel', StateFilter(QuizSessionFSM.nickname_retrieval))
async def process_cancel_name_input(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.callback_query(F.data == 'cancel', StateFilter(QuizSessionFSM.host_waiting_for_participants))
async def process_cancel_question_view_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_list_page = data['current_list_page']
    user_record_names = data['user_record_names']
    quiz_list_markup = create_list_of_q_or_t_markup(type_=Types.Quiz,
                                                    height=quiz_list_height,
                                                    page=current_list_page,
                                                    back_button_visible=True,
                                                    **user_record_names)
    await delete_code(data['session_id'])
    await cb.message.answer(text=LEXICON['your_quizzes'],
                            reply_markup=quiz_list_markup)
    await state.set_state(MainMenuFSM.q_or_t_list_view)
    await cb.message.delete()


@rt.callback_query(StateFilter(QuizSessionFSM.host_waiting_for_participants))
async def process_any_else_quiz_session_actions(cb: CallbackQuery):
    await cb.answer(text='Недоступное действие')
