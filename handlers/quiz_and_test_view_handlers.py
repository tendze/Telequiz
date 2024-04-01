from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.menu_keyboards import my_profile_markup
from factories import user_records
from states.states import MainMenuFSM, QuizSessionFSM
from database.db_services import *
from services.inline_keyboard_services import *
from handlers.quiz_and_test_list_height_config import quiz_list_height
from classes.question import Question
from observers.waiting_room_observer import room_observer
import utils
import mydatetime

rt = Router()


@rt.callback_query(F.data == 'go_back', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_go_back_press(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(text=LEXICON['my_profile'], reply_markup=my_profile_markup)


# Перемещение назад в просмотре списка квиза или теста
@rt.callback_query(F.data == 'backward', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_backwards_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_list_page = data['current_list_page']
    user_record_names = data['user_record_names']
    if current_list_page > 1:
        current_list_page -= 1
        quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz,
                                                        height=quiz_list_height,
                                                        page=current_list_page,
                                                        back_button_visible=True,
                                                        **user_record_names)
        await cb.message.edit_reply_markup(reply_markup=quiz_list_markup)
        await state.update_data(current_list_page=current_list_page)
    await cb.answer()


# Перемещение вперед в просмотре списка квиза или теста
@rt.callback_query(F.data == 'forward', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_forward_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_list_page = data['current_list_page']
    user_record_names = data['user_record_names']
    total_pages = data['total_pages']
    if current_list_page < total_pages:
        current_list_page += 1
        quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz,
                                                        height=quiz_list_height,
                                                        page=current_list_page,
                                                        back_button_visible=True,
                                                        **user_record_names)
        await cb.message.edit_reply_markup(reply_markup=quiz_list_markup)
        await state.update_data(current_list_page=current_list_page)
    await cb.answer()


@rt.callback_query(user_records.UserRecordsFactory.filter(), StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_record_press(cb: CallbackQuery, state: FSMContext, callback_data: user_records.UserRecordsFactory):
    data = await state.get_data()
    current_page = data['current_list_page']
    user_record_names = data['user_record_names']
    reset_reply_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz if callback_data.type_ == 'Q' else RecordTypes.Test,
                                                      height=quiz_list_height,
                                                      page=current_page,
                                                      back_button_visible=True,
                                                      **user_record_names)
    new_reply_markup = create_confirmation_button(inline_keyboard=reset_reply_markup,
                                                  callback_data=cb.data,
                                                  type_=callback_data.type_)
    record_id_pressed = callback_data.record_id
    await state.update_data(record_id=record_id_pressed)
    await cb.message.edit_reply_markup(reply_markup=new_reply_markup)


@rt.callback_query(F.data == 'cancel', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_cancel_record_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data['current_list_page']
    user_record_names = data['user_record_names']
    quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz,
                                                    height=quiz_list_height,
                                                    page=current_page,
                                                    back_button_visible=True,
                                                    **user_record_names)
    await cb.message.edit_reply_markup(reply_markup=quiz_list_markup)


@rt.callback_query(F.data == 'delete_record', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_delete_quiz_record_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    record_id_to_delete = data['record_id']
    current_page = data['current_list_page']
    user_record_names: dict[str, str] = data['user_record_names']
    try:
        await delete_user_record(record_id=record_id_to_delete)
        user_record_names.pop(str(record_id_to_delete))
        quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz,
                                                        height=quiz_list_height,
                                                        page=current_page,
                                                        back_button_visible=True,
                                                        **user_record_names)
        await cb.message.edit_reply_markup(reply_markup=quiz_list_markup)
    except Exception as e:
        await cb.answer('Произошла непредвиденная ошибка, не удалось удалить запись')
        print(e)


@rt.callback_query(F.data == 'view_record', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_view_quiz_press(cb: CallbackQuery, state: FSMContext):
    record_id = (await state.get_data())['record_id']
    questions: list[Question] = await get_user_record_questions(record_id=record_id)
    await state.update_data(questions=questions)
    await state.update_data(current_page=1)
    await state.update_data(list_text=cb.message.text)
    await state.update_data(list_inline_keyboard=cb.message.reply_markup.inline_keyboard)
    await state.set_state(MainMenuFSM.q_or_t_view)
    await cb.message.edit_text(
        text=questions[0].question,
        reply_markup=create_question_view_inline_markup(
            question=questions[0],
            current_question_index=1,
            all_question_count=len(questions)
        )
    )


# Перемещение назад в самом квизе или тесте
@rt.callback_query(F.data == 'backward', StateFilter(MainMenuFSM.q_or_t_view))
async def process_previous_question_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data['current_page']
    questions: list[Question] = data['questions']
    if current_page > 1:
        current_page -= 1
        await state.update_data(current_page=current_page)
        current_question = questions[current_page - 1]
        await cb.message.edit_text(
            text=current_question.question,
            reply_markup=create_question_view_inline_markup(
                question=current_question,
                current_question_index=current_page,
                all_question_count=len(questions)
            )
        )
    await cb.answer()


# Перемещение вперед в самом квизе или тесте
@rt.callback_query(F.data == 'forward', StateFilter(MainMenuFSM.q_or_t_view))
async def process_next_question_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data['current_page']
    questions: list[Question] = data['questions']
    if current_page < len(questions):
        current_page += 1
        await state.update_data(current_page=current_page)
        current_question = questions[current_page - 1]
        await cb.message.edit_text(
            text=current_question.question,
            reply_markup=create_question_view_inline_markup(
                question=current_question,
                current_question_index=current_page,
                all_question_count=len(questions)
            )
        )
    await cb.answer()


# Запуск квиза
@rt.callback_query(F.data == 'start_quiz', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_start_quiz_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_id: int = data['record_id']
    quiz_name: str = data['user_record_names'][str(quiz_id)]
    code: int = utils.quiz_utils.generate_code()
    deep_link = await utils.create_deep_link_by_code(code)
    timer_message = await cb.message.answer(
        text='<b>Тут будет таймер</b>'
    )
    msg = await cb.message.answer(
        text=f'<b>{quiz_name}</b>\nКод для присоединения <code>{code}</code>\n'
             f'Ссылка для присоедидения: {deep_link}\n'
             f'Количество участников 0',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[run_quiz_row, cancel_button_row])
    )
    session_id = await insert_code(
        code=code,
        user_id=cb.from_user.id,
        quiz_record_id=data['record_id'],
        time=mydatetime.get_time_now()
    )
    await room_observer.add_host_subscriber(
        code=code,
        message_id=msg.message_id,
        chat_id=msg.chat.id,
        host_state=state,
        session_id=session_id,
        quiz_name=quiz_name,
        timer_message_id=timer_message.message_id
    )
    await state.set_state(QuizSessionFSM.host_waiting_for_participants)
    await state.update_data(quiz_code=code)
    await cb.message.delete()


# Отправка теста на прохождение
@rt.callback_query(F.data == 'send_test', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_send_test_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    record_id = data['record_id']
    print(data)


# Отмена просмотра записи
@rt.callback_query(F.data == 'cancel', StateFilter(MainMenuFSM.q_or_t_view))
async def process_cancel_question_view_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(MainMenuFSM.q_or_t_list_view)
    await state.update_data(list_inline_keyboard={})
    await cb.message.edit_text(text=data['list_text'],
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=data['list_inline_keyboard']))
