from classes.quiz_participant import QuizParticipant
from services.inline_keyboard_services import *
from .base_quiz_observer import BaseQuizSessionObserver
from bot import bot
import utils


# Класс-наблюдатель. Отвечает за "live" обновление комнаты ожидания
# Подписчиком выступают id чата, id сообщения хоста и участника
class WaitingRoomObserver(BaseQuizSessionObserver):
    async def notify_subscribers(self, code):
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

    async def change_host_state(self, code, new_state):
        host: QuizParticipant = self.quiz_subscribers[code]['host']
        if host.user_state is not None:
            await host.user_state.set_state(new_state)

    async def change_all_participant_states(self, code, new_state):
        participants: list[QuizParticipant] = await self.get_all_participants(code)
        for participant in participants:
            if participant.user_state is not None:
                await participant.user_state.set_state(new_state)


room_observer = WaitingRoomObserver()
