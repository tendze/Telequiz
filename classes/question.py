from typing import Optional


class Question:
    def __init__(self, question: str,
                 variants=None,
                 right_variants=None,
                 photo_id: Optional[str] = None):
        if variants is None:
            variants: list[str] = []
        if right_variants is None:
            right_variants: set[str] = set()
        self.question = question
        self.variants = variants
        self.photo_id = photo_id
        self.right_variants = right_variants
