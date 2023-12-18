from Telequiz.types.question import Question


class Quiz:
    def __init__(self, name: str, questions: list[Question]):
        self.name = name
        self.questions = questions
