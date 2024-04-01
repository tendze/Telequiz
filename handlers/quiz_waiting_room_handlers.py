from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, CommandStart, CommandObject
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, ContentType

from database.db_services import *
from services.inline_keyboard_services import *
from states.states import *
from handlers.quiz_and_test_list_height_config import quiz_list_height
from lexicon.LEXICON_RU import LEXICON
from keyboards.menu_keyboards import main_menu_markup
from bot import bot
from observers.waiting_room_observer import room_observer
from observers.quiz_passing_observer import quiz_passing_observer
import asyncio

rt = Router()


# Обработка ввода кода по диплинку и по вводу вручную
@rt.message(StateFilter(QuizSessionFSM.code_retrieval))
async def process_deep_code_retrieval(message: Message, state: FSMContext, command: CommandObject = None):
    last_message_id = (await state.get_data())['last_message_id']
    quiz_code: str
    if command is not None:
        quiz_code = command.args
    else:
        quiz_code = message.text

    if not quiz_code.isdigit() or len(quiz_code) != 6:
        message = await message.answer(text=LEXICON['incorrect_code'],
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[cancel_button_row]))
        await state.update_data(last_message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
        return
    quiz_session_info = await get_quiz_session_info_by_code(quiz_code)
    if quiz_session_info is None:
        message = await message.answer(text=LEXICON['code_doesnt_exists'],
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[cancel_button_row]))
        await state.update_data(last_message_id=message.message_id)
    else:
        quiz_name = await get_user_record_info_by_id(quiz_session_info['quiz_record_id'])
        await message.answer(text=f'Сессия найдена:\n'
                                  f'<b>{quiz_name["name"]}</b>')
        which_inline_keyboard = nickname_confirmation_with_username_rows if message.from_user.username is not None \
            else nickname_confirmation_without_username_rows
        timer_message = await message.answer(
            text='<b>Тут будет таймер</b>'
        )
        message = await message.answer(
            text='Пришлите в чат свой собственный никнейм, не превышающий <u>30 символов</u>.',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=which_inline_keyboard
            )
        )
        await state.update_data(last_message_id=message.message_id)
        await state.update_data(timer_message_id=timer_message.message_id)
        await state.update_data(quiz_name=quiz_name['name'])
        await state.update_data(quiz_code=int(quiz_code))
        await state.set_state(QuizSessionFSM.nickname_retrieval)
    await bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)


# Обработка нажатия на кнопки "Использовать мой тэг" и "Использовать моё имя"
@rt.callback_query(F.data.in_({'use_my_name', 'use_my_tag'}), StateFilter(QuizSessionFSM.nickname_retrieval))
async def process_use_my_name_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_message_id = data['last_message_id']
    timer_message_id = data['timer_message_id']
    quiz_code = data['quiz_code']
    quiz_session_info = await get_quiz_session_info_by_code(quiz_code)
    if quiz_session_info is None:
        await cb.message.delete()
        message = await cb.message.answer(text=LEXICON['invalid_code'],
                                          reply_markup=InlineKeyboardMarkup(inline_keyboard=[cancel_button_row]))
        await state.update_data(last_message_id=message.message_id)
        await state.set_state(QuizSessionFSM.code_retrieval)
        return

    if cb.data == 'use_my_name':
        first_name = cb.from_user.first_name
        last_name = cb.from_user.last_name
        name = ("" if first_name is None else first_name) + " " + ("" if last_name is None else last_name)
    else:
        name = cb.from_user.username
    name_length = len(name)
    if name_length > 30 or name_length == 0:
        which_inline_keyboard = nickname_confirmation_with_username_rows if cb.from_user.username is not None \
            else nickname_confirmation_without_username_rows
        await bot.delete_message(chat_id=cb.message.chat.id, message_id=last_message_id)
        msg = await cb.message.answer(text=LEXICON['long_name_error'],
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=which_inline_keyboard))
        await state.update_data(last_message_id=msg.message_id)
        return
    if cb.data == 'use_my_tag':
        name = '@' + name
    quiz_name = data['quiz_name']

    msg = await cb.message.answer(text=f'<b>{quiz_name}</b>\n'
                                       f'Ожидайте пока организатор не запустит квиз.\n',
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[disconnect_quiz_row]))
    await room_observer.add_participant_subscriber(
        code=quiz_code,
        chat_id=cb.message.chat.id,
        message_id=msg.message_id,
        part_state=state,
        nickname=name,
        timer_message_id=timer_message_id
    )
    await bot.delete_message(chat_id=cb.message.chat.id, message_id=last_message_id)
    await state.update_data(last_message_id=msg.message_id)
    await state.set_state(QuizSessionFSM.participant_waiting_for_participants)
    await insert_participant(
        code=quiz_code,
        quiz_session_id=await room_observer.get_session_id(quiz_code),
        user_participant_id=cb.from_user.id
    )


# Обработка ввода кастомного имени
@rt.message(F.content_type == ContentType.TEXT, StateFilter(QuizSessionFSM.nickname_retrieval))
async def process_name_input(message: Message, state: FSMContext):
    data = await state.get_data()
    quiz_code = data['quiz_code']
    last_message_id = data['last_message_id']
    timer_message_id = data['timer_message_id']
    quiz_session_info = await get_quiz_session_info_by_code(quiz_code)
    if quiz_session_info is None:
        await message.delete()
        message = await message.answer(text=LEXICON['host_cancelled_quiz'] + "\nВведите новый код.",
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[cancel_button_row]))
        await state.update_data(last_message_id=message.message_id)
        await state.set_state(QuizSessionFSM.code_retrieval)
        return

    nick = message.text
    nick_length = len(nick)
    if nick_length > 30 or nick_length == 0 or '/' in nick:
        await bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
        which_inline_keyboard = nickname_confirmation_with_username_rows if message.from_user.username is not None else nickname_confirmation_without_username_rows
        msg = await message.answer(text=LEXICON['incorrect_name_30'],
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=which_inline_keyboard))
        await state.update_data(last_message_id=msg.message_id)
        return
    quiz_name = data['quiz_name']
    msg = await message.answer(text=f'<b>{quiz_name}</b>\n'
                                    f'Ожидайте пока организатор не запустит квиз.\n',
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[disconnect_quiz_row]))
    await room_observer.add_participant_subscriber(
        code=quiz_code,
        chat_id=message.chat.id,
        message_id=msg.message_id,
        part_state=state,
        nickname=nick,
        timer_message_id=timer_message_id
    )
    await bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
    await state.update_data(last_message_id=msg.message_id)
    await state.set_state(QuizSessionFSM.participant_waiting_for_participants)
    await insert_participant(
        code=quiz_code,
        quiz_session_id=await room_observer.get_session_id(quiz_code),
        user_participant_id=message.from_user.id
    )


# Отключение участника от квиза
@rt.callback_query(F.data == 'disconnect_quiz', StateFilter(QuizSessionFSM.participant_waiting_for_participants))
async def process_disconnect_quiz_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await room_observer.remove_participant(data['quiz_code'], cb.message.chat.id)
    await delete_participant(cb.from_user.id)


@rt.callback_query(F.data == 'run_quiz', StateFilter(QuizSessionFSM.host_waiting_for_participants))
async def process_run_quiz_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_code = data['quiz_code']
    participant_count = await room_observer.get_participant_count(code=quiz_code)
    if participant_count == 0:
        await cb.answer(text='Нельзя запускать квиз без участников')
        return
    record_id = data['record_id']
    questions: list[Question] = await get_user_record_questions(record_id)
    time_limit: int = await get_time_limit(record_id=record_id)
    await quiz_passing_observer.add_new_room(
        code=quiz_code,
        room=room_observer.quiz_subscribers[quiz_code],
        questions=questions,
        time_limit=time_limit
    )
    await room_observer.change_all_participant_states(code=quiz_code, new_state=QuizSessionFSM.participant_quiz_passing)
    await state.set_state(QuizSessionFSM.host_quiz_passing)
    del room_observer.quiz_subscribers[quiz_code]
    await quiz_passing_observer.next_question(code=quiz_code)
    await quiz_passing_observer.show_question(code=quiz_code)

    timer_task = asyncio.create_task(quiz_passing_observer.run_timer(code=quiz_code))
    await quiz_passing_observer.stop_timer(code=quiz_code)
    await quiz_passing_observer.set_timer_coroutine(code=quiz_code, timer_coroutine=timer_task)
    await timer_task


# Пришло какое либо сообщение во время ожидания запуска квиза организатором
@rt.message(StateFilter(QuizSessionFSM.participant_waiting_for_participants))
async def process_any_waiting_for_participants_action(message: Message):
    pass


# Отмена ввода кастомного имени
@rt.callback_query(F.data == 'cancel', StateFilter(QuizSessionFSM.nickname_retrieval))
async def process_cancel_name_input(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    timer_message_id = data['timer_message_id']
    await bot.delete_message(chat_id=cb.message.chat.id, message_id=timer_message_id)
    await state.clear()
    await cb.message.delete()
    await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


# Отмена сессии квиза
@rt.callback_query(F.data == 'cancel', StateFilter(QuizSessionFSM.host_waiting_for_participants))
async def process_cancel_question_view_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_code = data['quiz_code']
    current_list_page = data['current_list_page']
    user_record_names = data['user_record_names']
    quiz_list_markup = create_list_of_q_or_t_markup(type_=RecordTypes.Quiz,
                                                    height=quiz_list_height,
                                                    page=current_list_page,
                                                    back_button_visible=True,
                                                    **user_record_names)
    await delete_code(await room_observer.get_session_id(code=quiz_code))
    await room_observer.delete_room(quiz_code)
    await cb.message.answer(text=LEXICON['your_quizzes'],
                            reply_markup=quiz_list_markup)
    await state.set_state(MainMenuFSM.q_or_t_list_view)


# Все другие действия хоста
@rt.callback_query(StateFilter(QuizSessionFSM.host_waiting_for_participants))
async def process_any_else_quiz_session_actions(cb: CallbackQuery):
    await cb.answer(text='Недоступное действие')
