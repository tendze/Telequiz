from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter, CommandObject
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from keyboards.menu_keyboards import main_menu_markup, my_profile_markup
from states.states import *
from services.inline_keyboard_services import *
from services.keyboard_services import create_quiz_markup, create_test_markup
from database.db_services import *
from handlers.quiz_and_test_list_height_config import quiz_list_height
from handlers.statistics_list_height_config import statistics_list_height
from bot import bot
from mydatetime.datetime import parse_time, get_time_now_datetime
from handlers.quiz_waiting_room_handlers import process_deep_code_retrieval
from math import ceil
import utils
from factories import user_records, statistics_record
import sys

rt = Router()


# Обработка /start с параметром в виде ссылки на запись теста
@rt.message(
    CommandStart(
        deep_link=True,
        deep_link_encoded=True
    ),
    StateFilter(default_state, MainMenuFSM.q_or_t_list_view, MainMenuFSM.q_or_t_view, MainMenuFSM.confirmation)
)
async def process_start_command_with_test_link(message: Message, state: FSMContext, command: CommandObject):
    try:
        data = await state.get_data()
        last_message_id = data['last_message_id']
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=last_message_id
        )
        await state.clear()
    except Exception:
        pass
    decoded_arg = command.args
    data = decoded_arg.split(';')
    if len(data) != 3:
        return
    if not data[0].isdigit():
        await message.answer(
            text=LEXICON['incorrect_link']
        )
        return
    test_record_id = int(data[0])
    test_info = await get_user_record_info_by_id(id_=test_record_id)
    if test_info is None:
        await message.answer(
            text=LEXICON['invalid_link']
        )
        return
    deadline = parse_time(test_info['deadline'])
    time_now = get_time_now_datetime()
    if time_now > deadline:
        await message.answer(
            text=f'Дедлайн теста прошел уже прошел: <b>{test_info["deadline"]}</b>',
        )
        return
    msg = await message.answer(
        text=f'Пользователь <b>{data[1]}</b> приглашает вас пройти тест <b>{data[2]}\n'
             f'Вы можете пройти тест до: {test_info["deadline"]}</b>',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=agree_test_passing_rows)
    )
    await state.update_data(last_message_id=msg.message_id)
    await state.update_data(test_record_id=test_record_id)
    await state.update_data(test_info=test_info)
    await state.set_state(TestPassingFSM.test_passing_confirmation)


# Обработка /start с аргументом в виде кода сессиии
@rt.message(
    CommandStart(
        deep_link=True,
        deep_link_encoded=False
    ),
    StateFilter(default_state, MainMenuFSM.q_or_t_list_view, MainMenuFSM.q_or_t_view, MainMenuFSM.confirmation)
)
async def process_start_command_with_code(message: Message, state: FSMContext, command: CommandObject):
    try:
        data = await state.get_data()
        last_message_id = data['last_message_id']
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=last_message_id
        )
        await state.clear()
    except Exception:
        pass
    quiz_code = command.args
    if not quiz_code.isdigit() or len(quiz_code) != 6:
        msg = await message.answer(text=LEXICON['incorrect_arg_code'])
        await state.update_data(last_message_id=msg.message_id)
    else:
        await state.set_state(QuizSessionFSM.code_retrieval)
        msg = await message.answer(text='Обработка кода...')
        await state.update_data(last_message_id=msg.message_id)
        await process_deep_code_retrieval(message, state, command)


# Обработка команды /start.
@rt.message(
    CommandStart(),
    StateFilter(default_state, MainMenuFSM.q_or_t_list_view, MainMenuFSM.q_or_t_view, MainMenuFSM.confirmation)
)
async def process_start_command(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        last_message_id = data['last_message_id']
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=last_message_id
        )
        await state.clear()
    except Exception:
        pass
    await state.clear()
    await message.answer(text=LEXICON['greeting'])
    msg = await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.update_data(last_message_id=msg.message_id)


# Обработка команды /menu
@rt.message(
    Command(commands='menu'),
    StateFilter(default_state, MainMenuFSM)
)
async def process_menu_command(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        last_message_id = data['last_message_id']
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=last_message_id
        )
    except Exception as e:
        pass
    await state.clear()
    msg = await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.update_data(last_message_id=msg.message_id)


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
        await state.update_data(record_type='Q')
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
        await state.update_data(record_type='T')
        await state.update_data(user_record_names=user_quiz_names)
        await state.update_data(current_list_page=1)
        await state.update_data(total_pages=ceil(len(user_quiz_names) / quiz_list_height))
    await state.set_state(MainMenuFSM.q_or_t_list_view)
    await cb.answer()


@rt.callback_query(F.data == 'statistics', StateFilter(default_state))
async def process_statistics_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        text='Выберите какую статистику вы хотите посмотреть',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=statistics_choose_rows + [back_button_row])
    )
    await state.set_state(MainMenuFSM.statistics_select)


@rt.callback_query(F.data == 'for_quiz', StateFilter(MainMenuFSM.statistics_select))
async def process_for_quiz_statistics_view_button_press(
        cb: CallbackQuery,
        state: FSMContext,
        current_record_stat_page: int = None
):
    info = await get_statistics_info_by_id(cb.from_user.id, type_=RecordTypes.Quiz)
    if len(info) == 0:
        await cb.answer(text='К сожалению, у вас нет ни единой статистики по квизам.')
        return
    res = dict()
    for row in info:
        res[row['record_name']] = res.get(row['record_name'], {})
        res[row['record_name']][row['session_id']] = res[row['record_name']].get(row['session_id'], [])
        res[row['record_name']][row['session_id']].append(row)
    await cb.message.edit_text(
        text='Выберите квиз, для которого хотите посмотреть статистику',
        reply_markup=create_statistics_record_list_markup(
            info=res,
            height=statistics_list_height,
            type_=RecordTypes.Quiz,
            page=1 if current_record_stat_page is None else current_record_stat_page
        )
    )
    await state.update_data(statistics_info=res)
    await state.update_data(record_type='Q')
    await state.update_data(
        current_record_stat_page=1 if current_record_stat_page is None else current_record_stat_page
    )
    await state.set_state(MainMenuFSM.statistics_list_view)


@rt.callback_query(F.data == 'for_test', StateFilter(MainMenuFSM.statistics_select))
async def process_for_test_statistics_view_button_press(
        cb: CallbackQuery,
        state: FSMContext,
        current_record_stat_page: int = None
):
    info = await get_statistics_info_by_id(cb.from_user.id, type_=RecordTypes.Test)
    if len(info) == 0:
        await cb.answer(text='К сожалению, у вас нет ни единой статистики по тестам.')
        return
    res = dict()
    for row in info:
        res[row['record_name']] = res.get(row['record_name'], [])
        res[row['record_name']].append(row)
    await cb.message.edit_text(
        text='Выберите тест, для которого хотите посмотреть статистику',
        reply_markup=create_statistics_record_list_markup(
            info=res,
            height=statistics_list_height,
            type_=RecordTypes.Test,
            page=1 if current_record_stat_page is None else current_record_stat_page
        )
    )
    await state.update_data(statistics_info=res)
    await state.update_data(record_type='T')
    await state.update_data(
        current_record_stat_page=1 if current_record_stat_page is None else current_record_stat_page
    )
    await state.set_state(MainMenuFSM.statistics_list_view)


@rt.callback_query(factories.user_records.UserRecordsFactory.filter(), StateFilter(MainMenuFSM.statistics_list_view))
async def process_record_statistics_view_press(
        cb: CallbackQuery,
        state: FSMContext,
        callback_data: user_records.UserRecordsFactory,
        current_stat_page: int = None
):
    data = await state.get_data()
    record_name = await get_record_name_by_id(callback_data.record_id)
    statistics_info: dict = data['statistics_info'][record_name]
    if callback_data.type_ == 'Q':
        participants_count = sum([len(x) for x in statistics_info.values()])
        max_score = list(statistics_info.values())[0][0]['max_score']
        avg_score = sum([sum([y['score'] for y in x]) for x in statistics_info.values()]) / participants_count
    else:
        participants_count = len(statistics_info)
        max_score = statistics_info[0]['max_score']
        avg_score = sum(x['score'] for x in statistics_info) / participants_count

    if callback_data.type_ == 'T':
        stat_txt = f'<b>{record_name}</b>\n' \
               f'<b>Общая статистика:</b>\n' \
               f'Количество людей, прошедших тест: <b>{participants_count} чел.</b>\n' \
               f'Общий средний балл: <b>{avg_score:.3f} из {max_score}</b>'
    else:
        stat_txt = f'<b>{record_name}</b>\n' \
                   f'<b>Общая статистика:</b>\n' \
                   f'Количество людей, прошедших квиз: <b>{participants_count} чел.</b>\n' \
                   f'Всего проведено квизов: <b>{len(statistics_info)}</b>\n' \
                   f'Общий средний балл: <b>{avg_score:.3f} из {max_score}</b>'
    await cb.message.edit_text(
        text=stat_txt,
        reply_markup=create_statistics_list_markup(
            info=statistics_info,
            type_=RecordTypes.Quiz if callback_data.type_ == 'Q' else RecordTypes.Test,
            height=statistics_list_height,
            page=1 if current_stat_page is None else current_stat_page
        )
    )
    await state.update_data(record_name=record_name)
    await state.update_data(user_record_cb_data=callback_data)
    await state.update_data(current_stat_page=1 if current_stat_page is None else current_stat_page)
    await state.set_state(MainMenuFSM.specific_statistics_list_view)


@rt.callback_query(
    statistics_record.StatisticsRecordsFactory.filter(),
    StateFilter(MainMenuFSM.specific_statistics_list_view)
)
async def process_specific_statistics_button_press(
        cb: CallbackQuery,
        state: FSMContext,
        callback_data: statistics_record.StatisticsRecordsFactory
):
    data = await state.get_data()
    stats = data['statistics_info']
    record_name = data['record_name']
    session = stats[record_name]
    if callback_data.type_ == 'Q':
        stats = utils.quiz_utils.get_quiz_stats_by_session_info(session[callback_data.session_id])
        max_score = stats.max_score
        participant_list_str = "\n".join([f'<b>{i + 1}. {stats.participants[i][0]}</b> |' \
                                          f' <b>{(stats.participants[i][1])} из {max_score} |'
                                          f' {stats.participants[i][1] * 10 / max_score} из 10</b>'
                                          for i in range(len(stats.participants))])
        await cb.message.edit_text(
            text=f'<b>{record_name}</b>\n'
                 f'Список участников:\n'
                 f'<b>{participant_list_str}</b>',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[delete_button_row, back_button_row])
        )
    else:
        max_score = 0
        attempts = []
        nickname = await get_nickname_by_id(type_=RecordTypes.Test, id_=callback_data.id)
        for attempt in session:
            if attempt['nickname'] == nickname:
                max_score = attempt['max_score']
                attempts.append(attempt['score'])
        attempts_text = "\n".join([f'{i+1}. {attempts[i]} б.' for i in range(len(attempts))])
        await cb.message.edit_text(
            text=f'<b>{record_name}</b>\n'
                 f'<b>{nickname}</b>\n'
                 f'Максимально возможный балл теста: <b>{max_score}</b>\n'
                 f'Максимальный балл из всех попыток: <b>{max(attempts)}</b>\n'
                 f'Попытки:\n'
                 f'<b>{attempts_text}</b>',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[delete_button_row, back_button_row])
        )

    await state.update_data(stats_record_cb_data=callback_data)
    await state.set_state(MainMenuFSM.specific_statistics_view)


@rt.callback_query(F.data == 'delete', StateFilter(MainMenuFSM.specific_statistics_view))
async def process_delete_specific_stats_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cb_data: statistics_record.StatisticsRecordsFactory = data['stats_record_cb_data']
    type_ = cb_data.type_
    if type_ == 'Q':
        await delete_statistics_by_session_id(
            session_id=cb_data.session_id,
            type_=RecordTypes.Quiz
        )
    else:
        await delete_statistics_by_session_id(
            test_stat_id=cb_data.id,
            type_=RecordTypes.Test
        )
    await process_statistics_press(cb=cb, state=state)


@rt.callback_query(F.data == 'go_back', StateFilter(MainMenuFSM.statistics_select))
async def process_go_back_in_statistics_button_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text(text=LEXICON['my_profile'], reply_markup=my_profile_markup)
    await state.clear()


@rt.callback_query(F.data == 'go_back', StateFilter(MainMenuFSM.statistics_list_view))
async def process_go_back_statistics_list_view_button_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        text='Выберите какую статистику вы хотите посмотреть',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=statistics_choose_rows + [back_button_row])
    )
    await state.update_data(statistics_info={})
    await state.set_state(MainMenuFSM.statistics_select)


@rt.callback_query(F.data == 'go_back', StateFilter(MainMenuFSM.specific_statistics_list_view))
async def process_go_back_statistics_view_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    record_type: str = data['record_type']
    current_record_stat_page = data['current_record_stat_page']
    if record_type == 'Q':
        await process_for_quiz_statistics_view_button_press(cb, state, current_record_stat_page)
    else:
        await process_for_test_statistics_view_button_press(cb, state, current_record_stat_page)


@rt.callback_query(F.data == 'go_back', StateFilter(MainMenuFSM.specific_statistics_view))
async def process_go_back_statistics_view_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await process_record_statistics_view_press(cb=cb, state=state, callback_data=data['user_record_cb_data'])


@rt.callback_query(F.data == 'forward', ~StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_forward_page_button_press(cb: CallbackQuery, state: FSMContext):
    state_str = await state.get_state()
    data = await state.get_data()
    type_ = data['record_type']
    if state_str == 'MainMenuFSM:statistics_list_view':
        current_page = data['current_record_stat_page']
        info = data['statistics_info']
        total_pages = ceil(len(info) / statistics_list_height)
        current_page = total_pages if current_page == total_pages else current_page + 1
        try:
            await cb.message.edit_reply_markup(
                reply_markup=create_statistics_record_list_markup(
                    info=info,
                    height=statistics_list_height,
                    type_=RecordTypes.Quiz if type_ == 'Q' else RecordTypes.Test,
                    page=current_page
                )
            )
        except Exception:
            pass
        await state.update_data(current_record_stat_page=current_page)
    elif state_str == 'MainMenuFSM.specific_statistics_list_view':
        current_page = data['current_stat_page']
        record_name = data['record_name']
        info = data['statistics_info'][record_name]

        unique_info = []
        for i in info:
            nickname = i['nickname']
            for j in unique_info:
                if j['nickname'] == nickname:
                    break
            else:
                unique_info.append(i)
        info = unique_info
        total_pages = ceil(len(info) / statistics_list_height)
        current_page = total_pages if current_page == total_pages else current_page + 1
        try:
            await cb.message.edit_reply_markup(
                reply_markup=create_statistics_record_list_markup(
                    info=info,
                    height=statistics_list_height,
                    type_=RecordTypes.Quiz if type_ == 'Q' else RecordTypes.Test,
                    page=current_page
                )
            )
        except Exception:
            pass
        await state.update_data(current_stat_page=current_page)
    await cb.answer()


@rt.callback_query(F.data == 'backward', ~StateFilter(MainMenuFSM.q_or_t_list_view))
async def process_forward_page_button_press(cb: CallbackQuery, state: FSMContext):
    state_str = await state.get_state()
    data = await state.get_data()
    type_ = data['record_type']
    if state_str == 'MainMenuFSM:statistics_list_view':
        current_page = data['current_record_stat_page']
        info = data['statistics_info']
        current_page = (current_page - 1) if current_page > 1 else 1
        try:
            await cb.message.edit_reply_markup(
                reply_markup=create_statistics_record_list_markup(
                    info=info,
                    height=statistics_list_height,
                    type_=RecordTypes.Quiz if type_ == 'Q' else RecordTypes.Test,
                    page=current_page
                )
            )
        except Exception:
            pass
        await state.update_data(current_record_stat_page=current_page)
    elif state_str == 'MainMenuFSM.specific_statistics_list_view':
        current_page = data['current_stat_page']
        record_name = data['record_name']
        info = data['statistics_info'][record_name]
        current_page = (current_page - 1) if current_page > 1 else 1
        try:
            await cb.message.edit_reply_markup(
                reply_markup=create_statistics_record_list_markup(
                    info=info,
                    height=statistics_list_height,
                    type_=RecordTypes.Quiz if type_ == 'Q' else RecordTypes.Test,
                    page=current_page
                )
            )
        except Exception:
            pass
        await state.update_data(current_stat_page=current_page)
    await cb.answer()
