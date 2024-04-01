from typing import Optional


class Question:
    def __init__(
            self, question: str,
            variants=None,
            right_variants=None,
            consider_partial_answers: bool = False,
            photo_url: Optional[str] = None
    ):
        if variants is None:
            variants: list[str] = []
        if right_variants is None:
            right_variants: set[str] = set()
        self.question = question
        self.variants = variants
        self.consider_partial_answers = consider_partial_answers
        self.photo_url = photo_url
        self.right_variants = right_variants

    def __str__(self):
        return f'question:{self.question} | variants:{self.variants} | right_variants:{self.right_variants}'

    def __repr__(self):
        return f'Question:({self.__str__()})'