import random
import string

random.seed(random.randint(1, 1000))


def generate_code() -> str:
    digits = string.digits
    code = ''.join(random.sample(digits, 6))
    return code
