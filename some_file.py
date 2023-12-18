from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED, BaseFilter
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (Message, ContentType, ChatMemberUpdated, KeyboardButtonPollType,
                           InlineKeyboardMarkup, InputMediaAudio,
                           InputMediaDocument, InputMediaPhoto,
                           InputMediaVideo)
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, PhotoSize)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.web_app_info import WebAppInfo
from aiogram import F
from aiogram.exceptions import TelegramBadRequest
import copy
import asyncio
import os
from environs import Env
import logging
from typing import Optional

env = Env()
env.read_env()

redis = Redis(host='localhost')

storage = RedisStorage(redis=redis)

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Создаем "базу данных" пользователей


class Question:
    def __init__(self, question: str, variants: list[str], right_variants: list[str], photo_id: Optional[str] = None):
        self.question = question
        self.variants = variants
        self.photo_id = photo_id
        self.right_variants = right_variants


user_question_dict: dict[int, Question] = {}


class CreateQuiz(StatesGroup):
    GET_QUESTION_NAME = State()
    GET_VARIANTS = State()
    CHOOSE_RIGHT_ANSWERS = State()


class ShowMode(StatesGroup):
    QUESTION_ANSWERING = State()


class VariantsFactory(CallbackData, prefix='variants'):
    user_id: int
    var_number: int


def create_variants_inline_markup(variants: list[str], user_id: int, *more_buttons: InlineKeyboardButton) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for i in range(len(variants)):
        temp = [InlineKeyboardButton(text=variants[i],
                                     callback_data=VariantsFactory(user_id=user_id, var_number=i).pack())]
        buttons.append(temp)

    for button in more_buttons:
        temp = [button]
        buttons.append(temp)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_selected_button_markup(markup: InlineKeyboardMarkup, selected_button_data: str) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    for i in range(len(keyboard)):
        for j in range(len(keyboard[i])):
            if keyboard[i][j].callback_data == selected_button_data:
                if not keyboard[i][j].text.startswith('✓ '):
                    keyboard[i][j] = InlineKeyboardButton(text='✓ ' + keyboard[i][j].text,
                                                          callback_data=keyboard[i][j].callback_data)
                else:
                    keyboard[i][j] = InlineKeyboardButton(text=keyboard[i][j].text.lstrip('✓ '),
                                                          callback_data=keyboard[i][j].callback_data)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def is_any_button_checked(markup: InlineKeyboardMarkup) -> tuple[list[str], bool]:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    keyboard.pop()
    flag: bool = False
    right_answers: list[str] = []
    for row in keyboard:
        for button in row:
            if button.text.startswith("✓ "):
                flag = True
                right_answers.append(button.text.lstrip('✓ '))
    return right_answers, flag


def clean_variants_markup(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    for i in range(len(keyboard)):
        for j in range(len(keyboard[i])):
            if keyboard[i][j].text.startswith('✓ '):
                keyboard[i][j].text = keyboard[i][j].text.lstrip('✓ ')
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def is_checked_variants_right(markup: InlineKeyboardMarkup, right_answers: list[str]) -> bool:
    keyboard: list[list[InlineKeyboardButton]] = markup.inline_keyboard
    keyboard.pop()
    right_answer_checked_count: int = 0
    for row in keyboard:
        for button in row:
            text = button.text.lstrip("✓ ")
            if button.text != text and text in right_answers:
                right_answer_checked_count += 1
    if right_answer_checked_count != len(right_answers):
        return False
    return True


@dp.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext):
    await message.answer("Напишите текст вопроса")
    await state.set_state(CreateQuiz.GET_QUESTION_NAME)


@dp.message(StateFilter(CreateQuiz.GET_QUESTION_NAME), F.text)
async def process_get_name(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer(f"Текущий текст вопроса:\n {message.text}")
    await message.answer("Пришлите пожалуйста варианты вопросов через запятые, например:\n <вариант1>,"
                         "<вариант2>...\nТакже если хотите, чтобы к вопросу был прикреплено фото, пришлите его.")
    await state.set_state(CreateQuiz.GET_VARIANTS)


@dp.message(StateFilter(CreateQuiz.GET_QUESTION_NAME))
async def process_not_name(message: Message, state: FSMContext):
    await message.answer(text="Вы прислали точно не текст вопроса!!")


@dp.message(StateFilter(CreateQuiz.GET_VARIANTS), F.text)
async def process_get_variants(message: Message, state: FSMContext):
    variants = [x.strip(' ') for x in message.text.split(',')]
    await state.update_data(variants=variants)
    
    ready_button: InlineKeyboardButton = InlineKeyboardButton(text='Готово', callback_data='variants_ready')
    markup = create_variants_inline_markup(variants, message.from_user.id, ready_button)
    await message.answer("Отлично! Получили ваши варианты, теперь выберите какой ответ верный", reply_markup=markup)
    await state.set_state(CreateQuiz.CHOOSE_RIGHT_ANSWERS)


@dp.message(StateFilter(CreateQuiz.GET_VARIANTS), F.photo[-1].as_('photo'))
async def process_photo_send(message: Message, photo: PhotoSize, state: FSMContext):
    await state.update_data(photo_id=photo.file_id)
    await message.answer("Отлично! К вопросу будет прикреплено фото")


@dp.callback_query(StateFilter(CreateQuiz.CHOOSE_RIGHT_ANSWERS), VariantsFactory.filter())
async def process_right_answer_choose(cb: CallbackQuery, state: FSMContext):
    inline_markup: InlineKeyboardMarkup = cb.message.reply_markup
    await cb.message.edit_reply_markup(inline_message_id=cb.inline_message_id,
                                       reply_markup=create_selected_button_markup(inline_markup, cb.data))
    await cb.answer()


@dp.callback_query(StateFilter(CreateQuiz.CHOOSE_RIGHT_ANSWERS), F.data == 'variants_ready')
async def process_ready_button_press(cb: CallbackQuery, state: FSMContext):
    right_answers, is_any_checked = is_any_button_checked(cb.message.reply_markup)
    if not is_any_checked:
        await cb.message.answer("Пожалуйста, выберите правильный или правильные ответы!")
        await cb.answer()
    else:
        await cb.message.answer("Ваш вопрос создан! Теперь пришлите команду /show для демонстрации")
        data = await state.get_data()
        photo_id = data.get("photo_id", None)
        user_question_dict[cb.from_user.id] = Question(data['question'], data["variants"], right_answers, photo_id)
        await cb.answer()
        await state.clear()


@dp.message(Command(commands='show'), StateFilter(default_state))
async def process_show_command(message: Message, state: FSMContext):
    if user_question_dict.get(message.from_user.id, False):
        user_question: Question = user_question_dict[message.from_user.id]
        ready_button = InlineKeyboardButton(text="Ответить", callback_data="answer_the_question")
        markup = create_variants_inline_markup(user_question.variants, message.from_user.id, ready_button)
        await state.set_state(ShowMode.QUESTION_ANSWERING)
        if user_question.photo_id is None:
            await message.answer(text=user_question.question, reply_markup=markup)
        else:
            await message.answer_photo(photo=user_question.photo_id, caption=user_question.question, reply_markup=markup)
    else:
        await message.answer(text="Вы еще не создали вопрос, пришлите команду /start, чтобы создать свой вопрос")


@dp.callback_query(StateFilter(ShowMode.QUESTION_ANSWERING), VariantsFactory.filter())
async def process_button_question_answer_press(cb: CallbackQuery):
    inline_markup: InlineKeyboardMarkup = cb.message.reply_markup
    await cb.message.edit_reply_markup(inline_message_id=cb.inline_message_id,
                                       reply_markup=create_selected_button_markup(inline_markup, cb.data))
    await cb.answer()


@dp.callback_query(StateFilter(ShowMode.QUESTION_ANSWERING), F.data == 'answer_the_question')
async def process_answer_button_press(cb: CallbackQuery, state: FSMContext):
    question: Question = user_question_dict[cb.from_user.id]
    right_variants: list[str] = question.right_variants
    is_right = is_checked_variants_right(cb.message.reply_markup, right_variants)
    if is_right:
        await cb.message.answer(text="Вы правильно ответили поздравляю!")
        await cb.answer()
        await state.clear()
    else:
        temp: str = '\n✓ '.join(right_variants)
        await cb.message.answer(text=f"Вы неправильно ответили! Верными вариантами ответа были:\n{temp}")
        await cb.answer()
        await state.clear()


# хэндлер реагирующий на то, что пользователь кинул тебя в чс
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated):
    print(f'Пользователь {event.from_user.first_name} с id {event.from_user.id} заблокировал бота')


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
