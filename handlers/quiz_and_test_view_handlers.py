from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.menu_keyboards import my_profile_markup
from factories import user_records
from states.states import MainMenuFSM, QuizSessionFSM, CreateQuizOrTestFSM
from database.db_services import *
from services.inline_keyboard_services import *
from handlers.quiz_and_test_list_height_config import quiz_list_height
from classes.question import Question
from observers.waiting_room_observer import room_observer
from aiogram_dialog import DialogManager, StartMode
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
        record_type = data['record_type']
        quiz_list_markup = create_list_of_q_or_t_markup(
            type_=RecordTypes.Quiz if record_type == 'Q' else RecordTypes.Test,
            height=quiz_list_height,
            page=current_list_page,
            back_button_visible=True,
            **user_record_names
        )
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
        record_type = data['record_type']
        quiz_list_markup = create_list_of_q_or_t_markup(
            type_=RecordTypes.Quiz if record_type == 'Q' else RecordTypes.Test,
            height=quiz_list_height,
            page=current_list_page,
            back_button_visible=True,
            **user_record_names
        )
        await cb.message.edit_reply_markup(reply_markup=quiz_list_markup)
        await state.update_data(current_list_page=current_list_page)
    await cb.answer()


@rt.callback_query(user_records.UserRecordsFactory.filter(), StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_record_press(cb: CallbackQuery, state: FSMContext, callback_data: user_records.UserRecordsFactory,
                               record_name: str = None):
    record_info = await get_user_record_info_by_id(callback_data.record_id)
    info = f"Дедлайн: <b>{record_info['deadline']}</b>" if record_info['deadline'] is not None \
        else f'Временное ограничение: <b>{record_info["time_limit"]} секунд</b>'
    record_name = record_name if record_name is not None \
        else get_inline_button_text(inline_keyboard=cb.message.reply_markup, callback_data=cb.data)
    await state.update_data(record_name=record_name)
    new_reply_markup = create_record_confirmation_markup(
        type_=callback_data.type_
    )
    record_id_pressed = callback_data.record_id
    await state.update_data(record_id=record_id_pressed)
    await state.update_data(record_type=callback_data.type_)
    await cb.message.edit_text(
        text=f'<b>{record_name}</b>\n'
             f'{info}',
        reply_markup=new_reply_markup
    )


@rt.callback_query(F.data == 'cancel', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_cancel_confirmation_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data['current_list_page']
    user_record_names = data['user_record_names']
    record_type: str = data['record_type']
    reset_reply_markup = create_list_of_q_or_t_markup(
        type_=RecordTypes.Quiz if record_type == 'Q' else RecordTypes.Test,
        height=quiz_list_height,
        page=current_page,
        back_button_visible=True,
        **user_record_names
    )
    await cb.message.edit_text(
        text=LEXICON['your_quizzes'] if record_type == 'Q' else LEXICON['your_tests'],
        reply_markup=reset_reply_markup
    )


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
    deep_link = await utils.create_deep_link(param=code)
    timer_message = await cb.message.answer(
        text='<b>Тут будет таймер</b>'
    )
    msg = await cb.message.answer(
        text=f'<b>{quiz_name}</b>\nКод для присоединения <code>{code}</code>\n'
             f'Ссылка для присоедидения: {deep_link}\n'
             f'Количество участников 0',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[run_quiz_row, cancel_button_row])
    )
    time_now = mydatetime.get_time_now_str()
    session_id = await insert_code(
        code=code,
        user_id=cb.from_user.id,
        quiz_record_id=data['record_id'],
        time=time_now
    )
    await room_observer.add_host_subscriber(
        code=code,
        message_id=msg.message_id,
        chat_id=msg.chat.id,
        host_state=state,
        session_id=session_id,
        quiz_name=quiz_name,
        timer_message_id=timer_message.message_id,
        quiz_id=quiz_id,
        start_time=time_now
    )
    await state.set_state(QuizSessionFSM.host_waiting_for_participants)
    await state.update_data(quiz_code=code)
    await cb.message.delete()


# Отправка теста на прохождение
@rt.callback_query(F.data == 'send_test', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_send_test_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    record_id = data['record_id']
    record_info = await get_user_record_info_by_id(record_id)
    username_tag = cb.from_user.username
    if cb.from_user.username is not None:
        username = '@' + cb.from_user.username
    elif cb.from_user.first_name is None:
        username = cb.from_user.last_name
    elif cb.from_user.last_name is None:
        username = cb.from_user.first_name
    else:
        username = cb.from_user.first_name + cb.from_user.last_name

    inviter_nickname = username_tag if username_tag is not None else username
    inviter_nickname = '@' + inviter_nickname if username_tag is not None else inviter_nickname
    deep_link_param = str(record_info['record_id']) + ";" + inviter_nickname + ";" + record_info['name']
    test_deep_link = await utils.create_deep_link(param=deep_link_param, encode=True)
    await cb.message.answer(
        text=f'<b>{record_info["name"]}</b>\n'
             f'Ссылка на тест: {test_deep_link}'
    )
    await cb.answer()


# Отмена просмотра записи
@rt.callback_query(F.data == 'cancel', StateFilter(MainMenuFSM.q_or_t_view))
async def process_cancel_question_view_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(MainMenuFSM.q_or_t_list_view)
    await state.update_data(list_inline_keyboard={})
    await cb.message.edit_text(text=data['list_text'],
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=data['list_inline_keyboard']))


@rt.callback_query(F.data == 'change_deadline', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_change_deadline_button_press(cb: CallbackQuery, state: FSMContext, dialog_manager: DialogManager):
    await cb.message.delete()
    await cb.message.answer(text=f"Пожалуйста, выберите новый дедлайн")
    await state.set_state(CreateQuizOrTestFSM.get_deadline_state)
    await state.update_data(state_to_switch=MainMenuFSM.q_or_t_list_view)
    await dialog_manager.start(CreateQuizOrTestFSM.get_deadline_state, mode=StartMode.RESET_STACK)


@rt.callback_query(F.data == 'yes', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_yes_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    record_name = data['record_name']
    selected_date = data['selected_data']
    record_id = data['record_id']
    parsed_deadline = f'23:59 {selected_date.day}-{selected_date.month}-{selected_date.year}'
    await set_new_deadline(record_id=record_id, deadline=parsed_deadline)
    await process_record_press(
        cb=cb,
        state=state,
        callback_data=user_records.UserRecordsFactory(record_id=record_id, type_='T'),
        record_name=record_name
    )


@rt.callback_query(F.data == 'no', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_no_button_press(cb: CallbackQuery, state: FSMContext, dialog_manager: DialogManager):
    await state.set_state(CreateQuizOrTestFSM.get_deadline_state)
    await dialog_manager.start(CreateQuizOrTestFSM.get_deadline_state, mode=StartMode.NORMAL)


@rt.callback_query(F.data == 'change_time_limit', StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_change_time_limit_button_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await cb.message.answer(
        text='Пожалуйста, выберите новое временное ограничение на новый вопрос',
        reply_markup=time_limit_markup
    )
    await state.update_data(change_time_limit=True)
    await state.set_state(CreateQuizOrTestFSM.get_time_limit_state)
