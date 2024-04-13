from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import ContentType, Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database.db_services import insert_questions, RecordTypes, set_new_time_limit
from classes.question import Question
from lexicon.LEXICON_RU import LEXICON
from keyboards.menu_keyboards import main_menu_markup
from services.inline_keyboard_services import time_limit_markup
from states.states import CreateQuizOrTestFSM, MainMenuFSM
from .quiz_and_test_view_handlers import process_record_press
from aiogram_dialog import DialogManager, StartMode
from keyboards.calendar_keyboard import calendar_dialog
from factories import user_records
import json

rt = Router()
rt.include_router(calendar_dialog)


# Обработка получения данных из WebApp
@rt.message(F.content_type == ContentType.WEB_APP_DATA, StateFilter(CreateQuizOrTestFSM.create_or_cancel_state))
async def web_app(message: Message, state: FSMContext, dialog_manager: DialogManager):
    type_: RecordTypes = (await state.get_data())['type']
    result = json.loads(message.web_app_data.data)
    questions = [Question(question=q['question'],
                          variants=q['variants'],
                          right_variants=q['right_variants'],
                          consider_partial_answers=q['consider_partial_answers'] == 1) for q in result['questions']]
    await state.update_data(name=result['name'])
    await state.update_data(questions=questions)
    if type_ == RecordTypes.Quiz:
        await message.answer(text=LEXICON['choose_time_limit'], reply_markup=time_limit_markup)
        await state.set_state(CreateQuizOrTestFSM.get_time_limit_state)
        return
    try:
        await message.answer(text=f"Пожалуйста, выберите дедлайн для этого теста",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(CreateQuizOrTestFSM.get_deadline_state)
        await state.update_data(state_to_switch=CreateQuizOrTestFSM.deadline_confirmation_state)
        await dialog_manager.start(CreateQuizOrTestFSM.get_deadline_state, mode=StartMode.RESET_STACK)
    except Exception as e:
        print(f'Ошибка {e} в WebApp')
        await message.answer(text="Произошла непредвиденная ошибка :(",
                             reply_markup=ReplyKeyboardRemove())
        await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


# Обработка нажатия на кнопку "Готово" при выборе временного ограничения
@rt.callback_query(F.data == 'ready', StateFilter(CreateQuizOrTestFSM.get_time_limit_state))
async def process_ready_press(cb: CallbackQuery, state: FSMContext):
    timer_info = cb.message.reply_markup.inline_keyboard[0][2].text.split()
    seconds = int(timer_info[0])
    data = await state.get_data()
    if data.get('change_time_limit', False):
        record_name = data['record_name']
        record_id = data['record_id']
        await state.set_state(MainMenuFSM.q_or_t_list_view)
        await set_new_time_limit(record_id=record_id, seconds=seconds)
        await state.update_data(change_time_limit=False)
        await process_record_press(
            cb=cb,
            state=state,
            callback_data=user_records.UserRecordsFactory(record_id=record_id, type_='Q'),
            record_name=record_name
        )
        return
    try:
        await insert_questions(user_tg_id=cb.from_user.id,
                               name=data['name'],
                               questions=data['questions'],
                               type_=data['type'],
                               quiz_timer=seconds)
        await cb.message.answer(text="Квиз успешно создан!", reply_markup=ReplyKeyboardRemove())
        await cb.message.delete()
        await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    except Exception as e:
        print(f'Ошибка {e} в Ready')
        await cb.message.answer(text="Произошла непредвиденная ошибка :(",
                                reply_markup=ReplyKeyboardRemove())
        await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.clear()


# Обработка нажатия на кнопку изменения временного ограничения
@rt.callback_query(StateFilter(CreateQuizOrTestFSM.get_time_limit_state))
async def process_time_limit_press(cb: CallbackQuery):
    timer_info = cb.message.reply_markup.inline_keyboard[0][2].text.split()
    seconds = int(timer_info[0])  # секунды
    if cb.data == 'double_backward':
        if seconds >= 10:
            seconds -= 5
        else:
            await cb.answer(text='Минимальное время - 5 секунд')
            return
    elif cb.data == 'backward':
        if seconds >= 6:
            seconds -= 1
        else:
            await cb.answer(text='Минимальное время - 5 секунд')
            return
    elif cb.data == 'forward':
        if seconds <= 60:
            seconds += 1
        else:
            await cb.answer('Максимальное время - 60 секунд')
            return
    elif cb.data == 'double_forward':
        if seconds <= 55:
            seconds += 5
        else:
            await cb.answer('Максимальное время - 60 секунд')
            return
    timer_info_inline_keyboard = cb.message.reply_markup.inline_keyboard
    timer_info_inline_keyboard[0][2].text = str(seconds) + ' сек.'
    timer_info_markup = InlineKeyboardMarkup(inline_keyboard=timer_info_inline_keyboard)
    await cb.message.edit_reply_markup(reply_markup=timer_info_markup)


@rt.callback_query(F.data == 'no', StateFilter(CreateQuizOrTestFSM.deadline_confirmation_state))
async def process_no_button_press(cb: CallbackQuery, state: FSMContext, dialog_manager: DialogManager):
    await state.set_state(CreateQuizOrTestFSM.get_deadline_state)
    await dialog_manager.start(CreateQuizOrTestFSM.get_deadline_state, mode=StartMode.NORMAL)


@rt.callback_query(F.data == 'yes', StateFilter(CreateQuizOrTestFSM.deadline_confirmation_state))
async def process_yes_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    questions = data['questions']
    type_: RecordTypes = (await state.get_data())['type']
    selected_date = data['selected_data']
    parsed_deadline = f'23:59 {selected_date.day}-{selected_date.month}-{selected_date.year}'
    await insert_questions(
        user_tg_id=cb.from_user.id,
        name=name,
        questions=questions,
        type_=type_,
        quiz_timer=0,
        deadline=parsed_deadline
    )
    await state.clear()
    await cb.answer(text='Тест успешно создан!')
    await cb.message.delete()
    await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
