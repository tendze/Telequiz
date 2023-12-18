from typing import Optional


class Question:
    def __init__(self, question: str, variants: list[str], right_variants: list[str] = None, photo_id: Optional[str] = None):
        self.question = question
        self.variants = variants
        self.photo_id = photo_id
        self.right_variants = right_variants
