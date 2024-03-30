from aiogram.fsm.context import FSMContext

from classes.quiz_participant import QuizParticipant
from services.inline_keyboard_services import *
from keyboards.menu_keyboards import main_menu_markup
from bot import bot
import utils


# Класс реализовывающий паттерн "Наблюдатель"
# Подписчиком выступают id чата, id сообщения хоста и участника
class RoomObserver:
    def __init__(self):
        self.quiz_subscribers = dict()

    async def add_host_subscriber(
            self,
            code: int,
            chat_id: int,
            message_id: int,
            host_state: FSMContext,
            session_db_id: int,
            quiz_name: str = None
    ):
        if code not in self.quiz_subscribers:
            self.quiz_subscribers[code] = dict()
        self.quiz_subscribers[code]['session_id'] = session_db_id
        self.quiz_subscribers[code]['host'] = QuizParticipant(
            chat_id=chat_id,
            message_id=message_id,
            user_state=host_state
        )
        self.quiz_subscribers[code]['quiz_name'] = quiz_name

    async def add_participant_subscriber(
            self,
            code: int,
            chat_id: int,
            message_id: int,
            nickname: str,
            part_state: FSMContext
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
                nickname=nickname
            )
        )
        await self.notify_subscribers(code=code)

    async def delete_room(self, code):
        if code not in self.quiz_subscribers:
            return
        host: QuizParticipant = self.quiz_subscribers[code]['host']
        await bot.delete_message(chat_id=host.chat_id, message_id=host.message_id)
        participants_list: list[QuizParticipant] = await self.get_all_participants(code=code)
        for participant in participants_list:
            await participant.user_state.clear()
            await bot.delete_message(chat_id=participant.chat_id,
                                     message_id=participant.message_id)
            await bot.send_message(text=LEXICON['host_canceled_quiz'],
                                   chat_id=participant.chat_id)
            await bot.send_message(text=LEXICON['main_menu'],
                                   reply_markup=main_menu_markup,
                                   chat_id=participant.chat_id)
        del self.quiz_subscribers[code]

    async def notify_subscribers(self, code):
        print(self.quiz_subscribers)
        host: QuizParticipant = self.quiz_subscribers[code]['host']
        participants_list: list[QuizParticipant] = await room_observer.get_all_participants(code=code)
        participants_str_list = [f"{i + 1}. {participants_list[i].nickname}" for i in range(len(participants_list))]
        participants_str = "\n".join(participants_str_list)
        deep_link: str = await utils.create_deep_link_by_code(code)
        await bot.edit_message_text(
            text=f'<b>{self.quiz_subscribers[code]["quiz_name"]}</b>\n'
                 f'Код для присоединения <code>{code}</code>\n'
                 f'Ссылка для присоединения: {deep_link}\n'
                 f'Количество участников {await self.get_participant_count(code=code)}\n'
                 f'{participants_str}',
            chat_id=host.chat_id,
            message_id=host.message_id,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[run_quiz_row, cancel_button_row]
            )
        )

        participants: list[QuizParticipant] = self.quiz_subscribers[code]['participants']
        for participant in participants:
            await bot.edit_message_text(
                text=f'Ожидайте пока организатор не запустит квиз.\n'
                     f'{participants_str}',
                chat_id=participant.chat_id,
                message_id=participant.message_id,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[disconnect_quiz_row])
            )

    async def remove_participant(self, code, chat_id):
        new_list = list(
            filter(
                lambda participant: participant.chat_id != chat_id, self.quiz_subscribers[code]['participants']
            )
        )
        self.quiz_subscribers[code]['participants'] = new_list
        await self.notify_subscribers(code)

    async def get_all_participants(self, code) -> list[QuizParticipant]:
        return self.quiz_subscribers.get(code, {}).get('participants', [])

    async def get_participant_count(self, code) -> int:
        return len(self.quiz_subscribers.get(code, {}).get('participants', []))

    async def get_session_id(self, code) -> int:
        return self.quiz_subscribers.get(code, {}).get('session_id', -1)


room_observer = RoomObserver()
