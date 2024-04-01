from .base_quiz_observer import BaseQuizSessionObserver
from classes.quiz_participant import QuizParticipant
from services.inline_keyboard_services import *
from classes.question import Question
from keyboards.menu_keyboards import main_menu_markup
from bot import bot
import utils
import asyncio
import logging


# Класс-наблюдатель. Отвечает за "live" обновление вопросов квиза
# Подписчиком выступают id чата, id сообщения хоста и участника
class QuizPassingObserver(BaseQuizSessionObserver):
    async def notify_subscribers(self, code):
        pass

    async def add_new_room(
            self,
            code,
            room: dict,
            questions: list[Question],
            time_limit: int
    ):
        self.quiz_subscribers[code] = room
        self.quiz_subscribers[code]['questions'] = questions
        self.quiz_subscribers[code]['user_answers'] = dict()
        self.quiz_subscribers[code]['time_limit'] = time_limit

    async def finish_quiz(
            self,
            code
    ):
        host: QuizParticipant = self.quiz_subscribers[code]['host']
        await bot.delete_message(
            chat_id=host.chat_id,
            message_id=host.timer_message_id
        )
        await bot.edit_message_text(
            text='🎉Квиз завершён🎉\n Вы можете посмотреть статистику участников в вашем профиле',
            chat_id=host.chat_id,
            message_id=host.message_id
        )
        await host.user_state.clear()
        await bot.send_message(
            text=LEXICON['main_menu'],
            reply_markup=main_menu_markup,
            chat_id=host.chat_id,
        )

        participants_list: list[QuizParticipant] = await quiz_passing_observer.get_all_participants(code=code)
        questions: list[Question] = quiz_passing_observer.quiz_subscribers[code]['questions']
        for participant in participants_list:
            user_result = round(
                utils.quiz_utils.get_stats(
                    questions=questions,
                    user_answers=self.quiz_subscribers[code]['user_answers'].get(participant.chat_id, dict())
                ),
                3
            )
            await bot.delete_message(
                chat_id=participant.chat_id,
                message_id=participant.timer_message_id
            )
            await bot.edit_message_text(
                text=f'🎉Квиз завершён🎉\n'
                     f'Вы набрали <u>{user_result}</u> баллов из {len(questions)}',
                chat_id=participant.chat_id,
                message_id=participant.message_id
            )
            await participant.user_state.clear()
            await bot.send_message(
                text=LEXICON['main_menu'],
                reply_markup=main_menu_markup,
                chat_id=participant.chat_id,
            )
        print(self.quiz_subscribers[code])
        del self.quiz_subscribers[code]

    async def run_timer(self, code):
        host: QuizParticipant = self.quiz_subscribers[code]['host']
        participants: list[QuizParticipant] = self.quiz_subscribers[code]['participants']
        time_limit_secs = self.quiz_subscribers[code]['time_limit']
        try:
            seconds_remains = time_limit_secs
            for i in range(time_limit_secs + 1):
                seconds_remains_text = f'❗️<b>Осталось <u>{seconds_remains}</u> секунд</b>❗️'
                try:
                    await bot.edit_message_text(
                        text=seconds_remains_text,
                        chat_id=host.chat_id,
                        message_id=host.timer_message_id
                    )
                    for participant in participants:
                        await bot.edit_message_text(
                            text=seconds_remains_text,
                            chat_id=participant.chat_id,
                            message_id=participant.timer_message_id
                        )
                except Exception:
                    logging.info("INFO:Timer message not found")
                    return
                await asyncio.sleep(1)
                seconds_remains -= 1
            self.quiz_subscribers[code]['can_answer'] = False
        except asyncio.CancelledError:
            self.quiz_subscribers[code]['can_answer'] = True

    async def stop_timer(self, code):
        if 'timer' not in self.quiz_subscribers[code]:
            return
        self.quiz_subscribers[code]['timer'].cancel()

    async def show_question(self, code) -> bool:
        question_index = self.quiz_subscribers[code]['question_index']
        self.quiz_subscribers[code]['question_index'] = question_index
        questions: list[Question] = self.quiz_subscribers[code]['questions']
        if question_index >= len(questions) or question_index < 0:
            return False
        self.quiz_subscribers[code]['can_answer'] = True
        host: QuizParticipant = self.quiz_subscribers[code]['host']
        variant_buttons = create_quiz_variants_buttons(questions[question_index])
        host_markup = InlineKeyboardMarkup(
            inline_keyboard=variant_buttons + [line_button_row, next_question_row, finish_quiz_button_row]
        )

        await bot.edit_message_text(
            chat_id=host.chat_id,
            message_id=host.message_id,
            text=questions[question_index].question,
            reply_markup=host_markup
        )

        participants_list: list[QuizParticipant] = await quiz_passing_observer.get_all_participants(code=code)

        for participant in participants_list:
            participant_markup = InlineKeyboardMarkup(
                inline_keyboard=variant_buttons + [line_button_row, participant_answer_question_row,
                                                   disconnect_quiz_row]
            )
            await bot.edit_message_text(
                chat_id=participant.chat_id,
                message_id=participant.message_id,
                text=questions[question_index].question,
                reply_markup=participant_markup
            )
        return True

    async def next_question(self, code):
        self.quiz_subscribers[code]['question_index'] = self.quiz_subscribers[code].get('question_index', -1) + 1

    async def reset_index(self, code):
        self.quiz_subscribers[code]['question_index'] = -1

    async def get_current_question_index(self, code) -> int:
        return self.quiz_subscribers[code]['question_index']

    async def set_user_selected_answer(
            self,
            code,
            chat_id,
            question_index,
            var_indexes: list[int]
    ):
        if chat_id not in self.quiz_subscribers[code]['user_answers']:
            self.quiz_subscribers[code]['user_answers'][chat_id] = dict()
        self.quiz_subscribers[code]['user_answers'][chat_id][question_index] = var_indexes

    async def get_user_selected_answer_indexes(
            self,
            code,
            chat_id,
            question_index,
    ) -> list[int]:
        if chat_id not in self.quiz_subscribers[code]['user_answers'] \
                or question_index not in self.quiz_subscribers[code]['user_answers'][chat_id]:
            return []
        return self.quiz_subscribers[code]['user_answers'][chat_id][question_index]

    async def can_answer(self, code):
        return self.quiz_subscribers[code]['can_answer']

    async def set_timer_coroutine(self, code, timer_coroutine):
        self.quiz_subscribers[code]['timer'] = timer_coroutine


quiz_passing_observer = QuizPassingObserver()
