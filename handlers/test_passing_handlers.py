from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.states import TestPassingFSM
from keyboards.menu_keyboards import main_menu_markup
from services.inline_keyboard_services import *
from database.db_services import *
from factories.variants import VariantsFactory
from observers.test_passing_observer import test_passing_observer
import mydatetime
import utils

rt = Router()


@rt.callback_query(F.data == 'refuse', StateFilter(TestPassingFSM.test_passing_confirmation))
async def process_refuse_button_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    msg = await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.clear()
    await state.update_data(last_message_id=msg.message_id)


@rt.callback_query(F.data == 'pass_test', StateFilter(TestPassingFSM.test_passing_confirmation))
async def process_pass_test_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    test_record_id = data['test_record_id']
    msg_id = data['last_message_id']
    time_now = mydatetime.get_time_now_str()
    questions = await get_user_record_questions(record_id=test_record_id)
    await test_passing_observer.add_subscriber(
        chat_id=cb.message.chat.id,
        message_id=msg_id,
        questions=questions
    )
    await test_passing_observer.show_question(chat_id=cb.message.chat.id)
    await state.set_state(TestPassingFSM.test_passing)
    await state.update_data(start_time=time_now)


@rt.callback_query(VariantsFactory.filter(), StateFilter(TestPassingFSM.test_passing))
async def process_variant_button_press(cb: CallbackQuery, state: FSMContext, callback_data: VariantsFactory):
    data = await state.get_data()
    deadline = mydatetime.parse_time(data['test_info']['deadline'])
    time_now = mydatetime.get_time_now_datetime()
    if time_now > deadline:
        await cb.answer(text="Дедлайн прошел, проверьте свои ответы и завершите тест!")
        return
    var_selected_index = callback_data.var_number
    markup = create_ticked_test_variants_buttons(cb.message.reply_markup, var_selected_index)
    answer_indexes = get_question_ticked_answers_indexes(markup)
    try:
        await cb.message.edit_text(
            reply_markup=markup,
            text=(await test_passing_observer.get_current_questions(cb.message.chat.id)).question
        )
    except Exception:
        pass
    await test_passing_observer.set_question_answered_indexes(chat_id=cb.message.chat.id, indexes=answer_indexes)


@rt.callback_query(F.data == 'next_question', StateFilter(TestPassingFSM.test_passing))
async def process_next_question_button_press(cb: CallbackQuery, state: FSMContext):
    await test_passing_observer.next_questions(chat_id=cb.message.chat.id)
    try:
        await test_passing_observer.show_question(chat_id=cb.message.chat.id)
    except Exception:
        pass
    await cb.answer()


@rt.callback_query(F.data == 'previous_question', StateFilter(TestPassingFSM.test_passing))
async def process_previous_question_press(cb: CallbackQuery, state: FSMContext):
    await test_passing_observer.previous_question(chat_id=cb.message.chat.id)
    try:
        await test_passing_observer.show_question(chat_id=cb.message.chat.id)
    except Exception:
        pass
    await cb.answer()


@rt.callback_query(F.data == 'finish_test', StateFilter(TestPassingFSM.test_passing))
async def process_finish_test_button_press(cb: CallbackQuery):
    not_answered_numbers = await test_passing_observer.get_not_answered_question_indexes(
        chat_id=cb.message.chat.id,
        numbers=True
    )
    warning = 'Вы ответили на все вопросы' if len(not_answered_numbers) == 0 \
        else f'Вы не ответили на вопросы с номерами: {", ".join(map(str, not_answered_numbers))}'
    await cb.message.answer(text=f'Вы уверены, что хотите завершить тест?\n'
                                 f'{warning}',
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[yes_no_confirmation_row]))
    await cb.answer()


@rt.callback_query(F.data == 'no', StateFilter(TestPassingFSM.test_passing))
async def process_no_button_press(cb: CallbackQuery):
    await cb.message.delete()


@rt.callback_query(F.data == 'yes', StateFilter(TestPassingFSM.test_passing))
async def process_yes_button_press(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    test_info = data['test_info']
    start_time = data['start_time']
    questions = await test_passing_observer.get_user_questions(cb.message.chat.id)
    user_answers: dict[int, list[int]] = await test_passing_observer.get_user_answers(cb.message.chat.id)
    user_results = utils.quiz_utils.get_score_by_stats(questions=questions, user_answers=user_answers)
    nickname = f'@{cb.from_user.username}' if cb.from_user.username\
                                              is not None else f'{cb.from_user.first_name} {cb.from_user.last_name}'
    await cb.message.answer(text=f'🎉Вы завершили тест🎉\n Вы набрали <b>{user_results}</b> из {len(questions)}')
    await test_passing_observer.finish_test(chat_id=cb.message.chat.id)

    await add_statistics(
        type_=RecordTypes.Test,
        participant_tg_id=cb.message.chat.id,
        host_tg_id=test_info['tg_id'],
        record_id=data['test_record_id'],
        nickname=nickname,
        record_name=test_info['name'],
        score=round(user_results, 3),
        max_score=len(questions),
        start_time=start_time
    )
    msg = await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.update_data(last_message_id=msg.message_id)
    await state.clear()
    await cb.message.delete()

