from aiogram.fsm.context import FSMContext

from classes.quiz_participant import QuizParticipant
from services.inline_keyboard_services import *
from classes.question import Question
from classes.test_participant import TestParticipant
from keyboards.menu_keyboards import main_menu_markup
from bot import bot


class TestPassingObserver:
    def __init__(self):
        self.test_subscribers: dict[int, TestParticipant] = dict()

    async def add_subscriber(self, chat_id, message_id, questions: list[Question]):
        self.test_subscribers[chat_id]: TestParticipant = TestParticipant(
            chat_id=chat_id,
            message_id=message_id,
            questions=questions,
            question_index=0
        )

    async def show_question(self, chat_id):
        tester = self.test_subscribers[chat_id]
        current_index = await self.get_current_question_index(chat_id)
        questions = self.test_subscribers[chat_id].questions
        buttons = create_variants_buttons(questions[current_index]) + \
                  [
                      line_button_row
                  ] + \
                  [
                      previous_question_row +
                      [InlineKeyboardButton(text=f'{current_index+1}/{len(questions)}', callback_data='question_number')] +
                      next_question_row,
                      finish_test_button_row
                  ]
        answer_indexes = self.test_subscribers[chat_id].answers_indexes
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=buttons)
        for i in range(len(answer_indexes[current_index])):
            markup = create_ticked_test_variants_buttons(
                markup,
                variant_ticked_number=answer_indexes[current_index][i]+1
            )
        await bot.edit_message_text(
            message_id=tester.message_id,
            chat_id=chat_id,
            text=questions[current_index].question,
            reply_markup=markup
        )

    async def next_questions(self, chat_id):
        current_index = await self.get_current_question_index(chat_id)
        if current_index == len(self.test_subscribers[chat_id].questions) - 1:
            return
        self.test_subscribers[chat_id].question_index += 1

    async def previous_question(self, chat_id):
        current_index = await self.get_current_question_index(chat_id)
        if current_index == 0:
            return
        self.test_subscribers[chat_id].question_index -= 1

    async def set_question_answered_indexes(self, chat_id, indexes: list[int]):
        current_index = await self.get_current_question_index(chat_id)
        self.test_subscribers[chat_id].answers_indexes[current_index] = indexes

    async def get_current_questions(self, chat_id) -> Question:
        return self.test_subscribers[chat_id].questions[await self.get_current_question_index(chat_id)]

    async def get_current_question_index(self, chat_id) -> int:
        return self.test_subscribers[chat_id].question_index

    async def get_questions_len(self, chat_id) -> int:
        return len(self.test_subscribers[chat_id].questions)

    async def get_user_answers(self, chat_id) -> dict[int, list[int]]:
        answers = self.test_subscribers[chat_id].answers_indexes
        filtered_answers = {k: v for k, v in answers.items() if len(v) != 0}
        return filtered_answers

    async def get_not_answered_question_indexes(self, chat_id, numbers: bool = False) -> list[int]:
        res = []
        for index, lst in self.test_subscribers[chat_id].answers_indexes.items():
            if len(lst) == 0:
                res.append(index + 1 if numbers else index)
        return res

    async def get_user_questions(self, chat_id) -> list[Question]:
        return self.test_subscribers[chat_id].questions

    async def finish_test(self, chat_id):
        try:
            participant = self.test_subscribers[chat_id]
            await bot.delete_message(
                chat_id=participant.chat_id,
                message_id=participant.message_id
            )
            del self.test_subscribers[chat_id]
        except Exception:
            pass


test_passing_observer = TestPassingObserver()
