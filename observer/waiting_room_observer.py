from classes.quiz_message import QuizUserMessage


# Класс реализовывающий паттерн "Наблюдатель"
# Подписчиком выступают id чата, id сообщения хоста и участника
class RoomObserver:
    def __init__(self):
        self.subscribers = dict()

    def add_host_subscriber(self, code: int, chat_id: int, message_id: int):
        self.subscribers[code]['host'] = QuizUserMessage(chat_id=chat_id, message_id=message_id)

    def add_participant_subscriber(self, code: int, chat_id: int, message_id: int):
        if len(self.subscribers[code].get('participants', [])) == 0:
            self.subscribers[code]['participants'] = []
        self.subscribers[code]['participants'].append(QuizUserMessage(chat_id=chat_id, message_id=message_id))

    def delete_room(self, code):
        self.subscribers[code].clear()


room_observer = RoomObserver()
