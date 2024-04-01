from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery

from factories.variants import VariantsFactory
from database.db_services import *
from services.inline_keyboard_services import *
from states.states import *
from lexicon.LEXICON_RU import LEXICON
from keyboards.menu_keyboards import main_menu_markup
from observers.quiz_passing_observer import quiz_passing_observer
from handlers.quiz_and_test_list_height_config import quiz_list_height
import asyncio

rt = Router()


# Обработка нажатия на кнопку с вариантом ответа участником
@rt.callback_query(VariantsFactory.filter(), StateFilter(QuizSessionFSM.participant_quiz_passing))
async def process_quiz_variant_press(cb: CallbackQuery, state: FSMContext, callback_data: VariantsFactory):
    data = await state.get_data()
    quiz_code = data['quiz_code']
    if not (await quiz_passing_observer.can_answer(code=quiz_code)):
        await cb.answer("Время истекло!")
        return

    can_change, new_kb = create_ticked_quiz_variants_buttons(
        keyboard=cb.message.reply_markup,
        variant_ticked_number=callback_data.var_number
    )
    if not can_change:
        await cb.answer(text='Вы уже не можете поменять ответ!')
        return
    selected_answers_indexes = get_quiz_question_ticked_answers_indexes(
        keyboard=new_kb
    )
    current_question_index = await quiz_passing_observer.get_current_question_index(code=quiz_code)
    await quiz_passing_observer.set_user_selected_answer(
        code=quiz_code,
        chat_id=cb.message.chat.id,
        question_index=current_question_index,
        var_indexes=selected_answers_indexes
    )
    try:
        await cb.message.edit_reply_markup(
            reply_markup=new_kb
        )
    except Exception:
        pass


# Обработка нажатия на кнопку с "Следующий вопрос" хостом
@rt.callback_query(F.data == 'next_question', StateFilter(QuizSessionFSM.host_quiz_passing))
async def process_next_question_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_code = data['quiz_code']
    await quiz_passing_observer.next_question(code=quiz_code)
    is_not_last_question = await quiz_passing_observer.show_question(code=quiz_code)
    if not is_not_last_question:
        await quiz_passing_observer.finish_quiz(code=quiz_code)
        return
    timer_task = asyncio.create_task(quiz_passing_observer.run_timer(code=quiz_code))
    await quiz_passing_observer.stop_timer(code=quiz_code)
    await quiz_passing_observer.set_timer_coroutine(code=quiz_code, timer_coroutine=timer_task)
    await timer_task


# Обработка нажатия на кнопку с "Завершить квиз" хостом
@rt.callback_query(F.data == 'finish_quiz', StateFilter(QuizSessionFSM.host_quiz_passing))
async def process_finish_quiz_host_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_code = data['quiz_code']
    current_list_page = data['current_list_page']
    user_record_names = data['user_record_names']
    quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz,
                                                    height=quiz_list_height,
                                                    page=current_list_page,
                                                    back_button_visible=True,
                                                    **user_record_names)
    await delete_code(await quiz_passing_observer.get_session_id(code=quiz_code))
    await quiz_passing_observer.delete_room(quiz_code)
    await cb.message.answer(text=LEXICON['your_quizzes'],
                            reply_markup=quiz_list_markup)
    await state.set_state(MainMenuFSM.q_or_t_list_view)


# Обработка нажатия на кнопку с "Ответить" участником
@rt.callback_query(F.data == 'answer_question', StateFilter(QuizSessionFSM.participant_quiz_passing))
async def process_answer_question_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_code = data['quiz_code']
    if not (await quiz_passing_observer.can_answer(code=quiz_code)):
        await cb.answer("Время истекло!")
        return
    new_markup = create_new_markup_with_button_text(
        keyboard=cb.message.reply_markup,
        cb_data_to_find='answer_question',
        new_button_text=LEXICON['blocked_answer'],
        new_cb_data='blocked_answer_question'
    )
    await cb.message.edit_reply_markup(
        reply_markup=new_markup
    )


# Обработка нажатия на кнопку с "Отключиться" участником
@rt.callback_query(F.data == 'disconnect_quiz', StateFilter(QuizSessionFSM.participant_quiz_passing))
async def process_quiz_disconnect_while_session_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await quiz_passing_observer.remove_participant(data['quiz_code'], cb.message.chat.id)
    await delete_participant(cb.from_user.id)


# Обработка нажатия на все остальные кнопки участником
@rt.callback_query(StateFilter(QuizSessionFSM.participant_quiz_passing))
async def process_any_action_in_quiz_passing(cb: CallbackQuery):
    await cb.answer()


# Обработка нажатия на все остальные кнопки хостом
@rt.callback_query(StateFilter(QuizSessionFSM.host_quiz_passing))
async def process_any_host_action_in_quiz_passing(cb : CallbackQuery):
    await cb.answer()
