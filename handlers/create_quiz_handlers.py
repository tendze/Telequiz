from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import F, Router

from Telequiz.states.states import CreateQuizFSM
from Telequiz.lexicon.LEXICON_RU import LEXICON
from Telequiz.keyboards.menu_keyboards import main_menu_markup
from Telequiz.types.question import Question
from Telequiz.services.inline_keyboard_services import create_constructor_inline_markup, create_selected_button_markup
from Telequiz.factories.variants import VariantsFactory

rt = Router()


@rt.message(Command(commands='cancel'), StateFilter(CreateQuizFSM))
async def process_cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.callback_query(F.data == 'cancel', StateFilter(CreateQuizFSM))
async def process_cancel_button(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await cb.answer()


@rt.message(F.text, StateFilter(CreateQuizFSM.get_quiz_name_state))
async def process_quiz_name_get(message: Message, state: FSMContext):
    await state.update_data(quiz_name=message.text)
    await message.answer("Отлично, название получено!")
    await message.answer(text='У вас пока нет вопросов, добавьте их', reply_markup=create_constructor_inline_markup())
    await state.set_state(CreateQuizFSM.constructor_menu_state)


@rt.message(StateFilter(CreateQuizFSM.get_quiz_name_state))
async def process_not_quiz_name(message: Message, state: FSMContext):
    await message.answer(text='Вы прислали точно не название\n'
                              'Если хотите завершить создавание пропишите команду <b>/cancel</b>')


@rt.callback_query(F.data == 'new_question', StateFilter(CreateQuizFSM.constructor_menu_state))
async def process_new_question_button(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CreateQuizFSM.get_question_state)
    await cb.message.answer(text='Пришлите текст вопроса')
    await cb.answer()


@rt.message(F.text, StateFilter(CreateQuizFSM.get_question_state))
async def process_question_get(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer('Пришлите варианты вопроса, разделенные символом <b>";"</b>\n'
                         'Например, &lt;вариант1&gt;;&lt;вариант2&gt;... Не более 4 вариантов')
    await state.set_state(CreateQuizFSM.get_variants_state)


@rt.message(StateFilter(CreateQuizFSM.get_question_state))
async def process_not_question(message: Message, state: FSMContext):
    await message.answer(text='Это точно не текст вопроса!')


@rt.message(F.text, StateFilter(CreateQuizFSM.get_variants_state))
async def process_variants_get(message: Message, state: FSMContext):
    data = await state.get_data()
    questions: list[Question] = data.get('questions', [])
    question = Question(question=data['question'], variants=message.text.split(';'))
    questions.append(question)
    await state.update_data(questions=questions)
    await message.answer(text='Успешно добавлен новый вопрос!\n'
                              'Не забудьте у каждого вопроса отметить правильные ответы')
    await state.update_data(current_question_index=len(questions) - 1)
    await message.answer(text=question.question,
                         reply_markup=create_constructor_inline_markup(question, False, True, len(questions), len(questions)))
    await state.set_state(CreateQuizFSM.constructor_menu_state)


@rt.message(StateFilter(CreateQuizFSM.get_variants_state))
async def process_not_variants(message: Message):
    await message.answer(text='Вы прислали точно не варианты ответов по требуемому шаблону!\n'
                              'Если хотите завершить создавание пропишите команду <b>/cancel</b>')


@rt.callback_query(F.data == 'backward', StateFilter(CreateQuizFSM.constructor_menu_state))
async def process_backwards_button(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions: list[Question] = data.get('questions', [])
    curr_question_index = data['current_question_index']
    if curr_question_index != 0:
        curr_question_index -= 1
        question = questions[curr_question_index]
        await state.update_data(current_question_index=curr_question_index)
        await cb.message.edit_text(
            text=question.question,
            reply_markup=create_constructor_inline_markup(question, False, True, curr_question_index + 1, len(questions))
        )
    await cb.answer()


@rt.callback_query(F.data == 'forward', StateFilter(CreateQuizFSM.constructor_menu_state))
async def process_backwards_button(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions: list[Question] = data.get('questions', [])
    curr_question_index = data['current_question_index']
    if curr_question_index != len(questions) - 1:
        curr_question_index += 1
        question = questions[curr_question_index]
        await state.update_data(current_question_index=curr_question_index)
        await cb.message.edit_text(
            text=question.question,
            reply_markup=create_constructor_inline_markup(question, False, True, curr_question_index + 1, len(questions))
        )
    await cb.answer()


@rt.callback_query(F.data == 'edit', StateFilter(CreateQuizFSM.constructor_menu_state))
async def process_edit_button(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions: list[Question] = data.get('questions', [])
    curr_question_index = data['current_question_index']
    question = questions[curr_question_index]
    await cb.message.edit_text(text=question.question,
                               reply_markup=create_constructor_inline_markup(question, True, True,
                                                                             curr_question_index + 1, len(questions)))
    await state.set_state(CreateQuizFSM.edit_variants_state)


@rt.callback_query(F.data == 'cancel_edit', StateFilter(CreateQuizFSM.edit_variants_state))
async def process_cancel_edit_button(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions: list[Question] = data.get('questions', [])
    curr_question_index = data['current_question_index']
    question = questions[curr_question_index]
    await cb.message.edit_text(text=question.question,
                               reply_markup=create_constructor_inline_markup(question, False, True,
                                                                             curr_question_index + 1, len(questions)))
    await state.set_state(CreateQuizFSM.constructor_menu_state)


@rt.callback_query(VariantsFactory.filter(), StateFilter(CreateQuizFSM.constructor_menu_state))
async def process_variants_press(cb: CallbackQuery, state: FSMContext, callback_data: VariantsFactory):
    data = await state.get_data()
    questions: list[Question] = data.get('questions', [])
    curr_question_index = data['current_question_index']
    variant_text = questions[curr_question_index].variants[callback_data.var_number]
    questions[curr_question_index].variants[callback_data.var_number] = \
        variant_text.lstrip(LEXICON['tick']) if variant_text.startswith(LEXICON['tick'])\
        else LEXICON['tick'] + variant_text
    question = questions[curr_question_index]
    await state.update_data(questions=questions)
    await cb.message.edit_reply_markup(reply_markup=create_constructor_inline_markup(question,
                                                                                     False,
                                                                                     True,
                                                                                     curr_question_index+1,
                                                                                     len(questions)))
    await cb.answer()


@rt.callback_query(VariantsFactory.filter(), StateFilter(CreateQuizFSM.edit_variants_state))
async def process_variants_delete_button(cb: CallbackQuery, state: FSMContext, callback_data: VariantsFactory):
    data = await state.get_data()
    questions: list[Question] = data.get('questions', [])
    curr_question_index = data['current_question_index']
    if len(questions[curr_question_index].variants) > 1:
        del questions[curr_question_index].variants[callback_data.var_number]
        await cb.message.edit_reply_markup(reply_markup=create_constructor_inline_markup(questions[curr_question_index],
                                                                                         True,
                                                                                         True,
                                                                                         curr_question_index + 1,
                                                                                         len(questions)))
    else:
        await cb.answer(text='Последний вопрос нельзя удалить\nВы можете только удалить вопрос полностью')
    await state.update_data(questions=questions)
