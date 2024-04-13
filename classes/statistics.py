class QuizSessionStatistics:
    def __init__(
            self,
            max_score: int,
            participants: list[tuple[str, int]],
            session_id: int
    ):
        self.max_score = max_score
        self.participants = participants
