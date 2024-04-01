import random
from observers.quiz_passing_observer import quiz_passing_observer
from classes.question import Question

random.seed(random.randint(1, 1000))


class QuizUtils:
    def generate_code(self) -> int:
        return random.randint(100000, 999999)

    # Считает баллы по количеству верных ответов
    def get_stats(
            self,
            questions: list[Question],
            user_answers: dict[int, list[int]]
    ) -> int:
        result = 0
        for i in range(len(questions)):
            if i not in user_answers:
                continue
            question = questions[i]
            if len(question.right_variants) == 1:
                if question.variants[user_answers[i][0]] in question.right_variants:
                    result += 1
            else:
                right_variants_ticked_count = 0
                for var_index in user_answers[i]:
                    variant_selected = question.variants[var_index]
                    if variant_selected in question.right_variants:
                        right_variants_ticked_count += 1
                if question.consider_partial_answers:
                    result += right_variants_ticked_count / len(question.variants)
                else:
                    result += 1 if right_variants_ticked_count == len(question.right_variants) else 0
        return result


quiz_utils = QuizUtils()
