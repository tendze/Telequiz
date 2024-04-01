from aiogram.fsm.context import FSMContext


# Класс, хранящий id чата и id сообщения
# используется для редактирования сообщения во время ожидания участников
class QuizParticipant:
    def __init__(
            self,
            chat_id: int,
            message_id: int,
            user_state: FSMContext,
            nickname: str = None,
            timer_message_id: int = None
    ):
        self.chat_id = chat_id
        self.message_id = message_id
        self.nickname = nickname
        self.user_state = user_state
        self.timer_message_id = timer_message_id

    def __str__(self):
        return f'chat:{self.chat_id},message_id:{self.message_id},nickname:{self.nickname},timer_message_id:{self.timer_message_id}'

    def __repr__(self):
        return f'QuizParticipant({self.__str__()})'
