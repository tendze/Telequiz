from aiogram.fsm.context import FSMContext

from classes.quiz_participant import QuizParticipant
from services.inline_keyboard_services import *
from keyboards.menu_keyboards import main_menu_markup
from bot import bot
import logging


# Базовый класс-наблюдатель за квизом
class BaseQuizSessionObserver:
    def __init__(self):
        self.quiz_subscribers = dict()

    async def add_host_subscriber(
            self,
            code: int,
            chat_id: int,
            message_id: int,
            host_state: FSMContext,
            session_id: int,
            quiz_id: int,
            start_time: str,
            quiz_name: str = None,
            timer_message_id: int = None,
    ):
        if code not in self.quiz_subscribers:
            self.quiz_subscribers[code] = dict()
        if 'participants' not in self.quiz_subscribers[code]:
            self.quiz_subscribers[code]['participants'] = []
        self.quiz_subscribers[code]['session_id'] = session_id
        self.quiz_subscribers[code]['host'] = QuizParticipant(
            chat_id=chat_id,
            message_id=message_id,
            user_state=host_state,
            timer_message_id=timer_message_id
        )
        self.quiz_subscribers[code]['record_id'] = quiz_id
        self.quiz_subscribers[code]['quiz_name'] = quiz_name
        self.quiz_subscribers[code]['start_time'] = start_time

    async def add_participant_subscriber(
            self,
            code: int,
            chat_id: int,
            message_id: int,
            nickname: str,
            part_state: FSMContext,
            timer_message_id: int = None
    ):
        if code not in self.quiz_subscribers:
            self.quiz_subscribers[code] = dict()
        if 'participants' not in self.quiz_subscribers[code]:
            self.quiz_subscribers[code]['participants'] = []
        self.quiz_subscribers[code]['participants'].append(
            QuizParticipant(
                chat_id=chat_id,
                message_id=message_id,
                user_state=part_state,
                nickname=nickname,
                timer_message_id=timer_message_id
            )
        )
        await self.notify_subscribers(code=code)

    async def delete_room(self, code):
        if code not in self.quiz_subscribers:
            return
        host: QuizParticipant = self.quiz_subscribers[code]['host']
        await bot.delete_message(chat_id=host.chat_id, message_id=host.timer_message_id)
        await bot.delete_message(chat_id=host.chat_id, message_id=host.message_id)
        participants_list: list[QuizParticipant] = await self.get_all_participants(code=code)
        for participant in participants_list:
            await participant.user_state.clear()
            try:
                await bot.delete_message(chat_id=participant.chat_id,
                                         message_id=participant.message_id)
                await bot.delete_message(chat_id=participant.chat_id,
                                         message_id=participant.timer_message_id)
                await bot.send_message(text=LEXICON['host_canceled_quiz'],
                                       chat_id=participant.chat_id)
                await bot.send_message(text=LEXICON['main_menu'],
                                       reply_markup=main_menu_markup,
                                       chat_id=participant.chat_id)
            except Exception as e:
                logging.info(e)
        del self.quiz_subscribers[code]

    async def notify_subscribers(self, code):
        raise NotImplementedError("BaseRoomObserver: method notify_subscribers is not overridden")

    async def remove_participant(self, code, chat_id):
        if code not in self.quiz_subscribers:
            return
        participant_to_remove: QuizParticipant = None
        for participant in self.quiz_subscribers[code]['participants']:
            participant_to_remove = participant if participant.chat_id == chat_id else None
        new_list = list(
            filter(
                lambda participant: participant.chat_id != chat_id, self.quiz_subscribers[code]['participants']
            )
        )
        self.quiz_subscribers[code]['participants'] = new_list
        if participant_to_remove is not None:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=participant_to_remove.message_id)
                await bot.delete_message(chat_id=chat_id, message_id=participant_to_remove.timer_message_id)
            except Exception:
                pass
        await self.notify_subscribers(code=code)

    async def get_all_participants(self, code) -> list[QuizParticipant]:
        return self.quiz_subscribers.get(code, {}).get('participants', [])

    async def get_participant_count(self, code) -> int:
        return len(self.quiz_subscribers.get(code, {}).get('participants', []))

    async def get_session_id(self, code) -> int:
        return self.quiz_subscribers.get(code, {}).get('session_id', -1)

    async def is_session_active(self, code) -> bool:
        return code in self.quiz_subscribers
