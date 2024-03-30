# Класс ,хранящий id чата и id сообщения
# используется для редактирования сообщения во время ожидания участников
class QuizUserMessage:
    def __init__(self, chat_id: int, message_id: int, name: str = None):
        self.chat_id = chat_id
        self.message_id = message_id
