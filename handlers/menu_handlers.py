from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from Telequiz.keyboards.menu_keyboards import main_menu_markup, my_profile_markup, cancel_markup
from Telequiz.lexicon.LEXICON_RU import LEXICON
from Telequiz.states.states import CreateQuizFSM

rt = Router()


@rt.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text=LEXICON['greeting'])
    await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.message(Command(commands='menu'), StateFilter(default_state))
async def process_menu_command(message: Message):
    await message.answer(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.message(Command(commands='about'), StateFilter(default_state))
async def process_info_command(message: Message):
    await message.answer(text=LEXICON['about_bot'])


@rt.callback_query(F.data == "my_profile", StateFilter(default_state))
async def process_profile_button_press(cb: CallbackQuery):
    await cb.message.edit_text(text=LEXICON['my_profile'], reply_markup=my_profile_markup)


@rt.callback_query(F.data == "back_main_menu", StateFilter(default_state))
async def process_back_press(cb: CallbackQuery):
    await cb.message.edit_text(text=LEXICON['main_menu'], reply_markup=main_menu_markup)


@rt.callback_query(F.data == "create_quiz", StateFilter(default_state))
async def process_create_quiz_press(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(text=f"<b>Придумайте и отправьте название квиза</b>\n\n"
                                 f"В любой момент Вы можете прописать команду "
                                 f"<b>/cancel</b> "
                                 f" или нажать на кнопку \"{LEXICON['cancel']}\", "
                                 "чтобы прекратить создавание квиза, но в таком случае квиз <u>не сохранится</u>",
                            reply_markup=cancel_markup)
    await state.set_state(CreateQuizFSM.get_quiz_name_state)
    await cb.answer()


@rt.callback_query()
async def process_other_buttons_press(cb: CallbackQuery, state: FSMContext):
    await cb.answer(text='Скоро будет :))')
