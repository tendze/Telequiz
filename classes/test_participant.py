from .question import Question


class TestParticipant:
    def __init__(
            self,
            chat_id: int,
            message_id: int,
            questions: list[Question],
            question_index: int
    ):
        self.chat_id = chat_id
        self.message_id = message_id
        self.questions = questions
        self.question_index = question_index
        self.answers_indexes: dict[int, list[int]] = {i: list() for i in range(len(questions))}

    def __str__(self):
        return f'chat_id:{self.chat_id}, questions:{self.questions}, index:{self.question_index}, answers:{self.answers_indexes}'

    def __repr__(self):
        return f'TestParticipant({self.__str__()})'
