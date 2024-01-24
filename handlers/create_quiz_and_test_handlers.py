from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import ContentType, Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database.db_services import insert_questions, Types
from classes.question import Question
from lexicon.LEXICON_RU import LEXICON
from keyboards.menu_keyboards import main_menu_markup
from services.inline_keyboard_services import time_limit_markup
from states.states import CreateQuizOrTestFSM

import json

rt = Router()


@rt.message(F.content_type == ContentType.WEB_APP_DATA, StateFilter(CreateQuizOrTestFSM.create_or_cancel_state))
async def web_app(message: Message, state: FSMContext):
    type_: Types = (await state.get_data())['type']
    result = json.loads(message.web_app_data.data)
    questions = [Question(question=q['question'],
                          variants=q['variants'],
                          right_variants=q['right_variants'],
                          consider_partial_answers=q['consider_partial_answers'] == 1) for q in result['questions']]
    if type_ == Types.Quiz:
        await message.answer(text=LEXICON['choose_time_limit'], reply_markup=time_limit_markup)
        await state.update_data(name=result['name'])
        await state.update_data(questions=questions)
        await state.set_state(CreateQuizOrTestFSM.get_time_limit_state)
        return
    try:
        await insert_questions(user_tg_id=message.from_user.id,
                               name=result['name'],
                               questions=questions,
                               type_=type_,
                               quiz_timer=0)
        await message.answer(text=f"Тест успешно создан!\n"
                                  f"Данные сохранены в Вашем профиле.",
                             reply_markup=ReplyKeyboardRemove())
        await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    except Exception:
        await message.answer(text="Произошла непредвиденная ошибка :(",
                             reply_markup=ReplyKeyboardRemove())
        await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.clear()


@rt.callback_query(F.data == 'ready', StateFilter(CreateQuizOrTestFSM.get_time_limit_state))
async def process_ready_press(cb: CallbackQuery, state: FSMContext):
    timer_info = cb.message.reply_markup.inline_keyboard[0][2].text.split()
    seconds = int(timer_info[0])
    data = await state.get_data()
    try:
        await insert_questions(user_tg_id=cb.from_user.id,
                               name=data['name'],
                               questions=data['questions'],
                               type_=data['type'],
                               quiz_timer=seconds)
        await cb.message.answer(text="Квиз успешно создан!")
        await cb.message.delete()
        await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    except Exception:
        await cb.message.answer(text="Произошла непредвиденная ошибка :(",
                                reply_markup=ReplyKeyboardRemove())
        await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.clear()


@rt.callback_query(StateFilter(CreateQuizOrTestFSM.get_time_limit_state))
async def process_time_limit_press(cb: CallbackQuery, state: FSMContext):
    timer_info = cb.message.reply_markup.inline_keyboard[0][2].text.split()
    seconds = int(timer_info[0])  # секунды
    time = timer_info[1]  # минуты или секунды
    if cb.data == 'double_backward':
        if seconds >= 10:
            seconds -= 5
        else:
            await cb.answer(text='Минимальное время - 5 секунд')
    elif cb.data == 'backward':
        if seconds >= 6:
            seconds -= 1
        else:
            await cb.answer(text='Минимальное время - 5 секунд')
    elif cb.data == 'forward':
        if seconds <= 60:
            seconds += 1
        else:
            await cb.answer('Максимальное время - 60 секунд')
    elif cb.data == 'double_forward':
        if seconds <= 55:
            seconds += 5
        else:
            await cb.answer('Максимальное время - 60 секунд')
    timer_info_inline_keyboard = cb.message.reply_markup.inline_keyboard
    timer_info_inline_keyboard[0][2].text = str(seconds) + ' сек.'
    timer_info_markup = InlineKeyboardMarkup(inline_keyboard=timer_info_inline_keyboard)
    await cb.message.edit_reply_markup(reply_markup=timer_info_markup)
