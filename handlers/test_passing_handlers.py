from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.states import MainMenuFSM, QuizSessionFSM, TestPassingFSM
from keyboards.menu_keyboards import main_menu_markup
from services.inline_keyboard_services import *

rt = Router()


@rt.callback_query(F.data == 'refuse', StateFilter(TestPassingFSM.test_passing_confirmation))
async def process_refuse_button_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    msg = await cb.message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)
    await state.clear()
    await state.update_data(last_message_id=msg.message_id)


@rt.callback_query(F.data == 'pass_test', StateFilter(TestPassingFSM.test_passing))
async def process_pass_test_button_press(cb: CallbackQuery, state: FSMContext):
    pass


