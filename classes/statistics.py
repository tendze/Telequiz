class QuizSessionStatistics:
    def __init__(
            self,
            max_score: int,
            participants: list[tuple[str, int]],
            session_id: int
    ):
        self.max_score = max_score
        self.participants = participants
        self.session_id = session_id

    def __str__(self):
        return f'max_score:{self.max_score} | participants:{self.participants} | session_id:{self.session_id}'

    def __repr__(self):
        return f'QuizSessionStatistics({self.__str__()})'
