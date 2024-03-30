import random

random.seed(random.randint(1, 1000))


def generate_code() -> int:
    return random.randint(100000, 999999)
