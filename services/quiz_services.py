import random
import string


def generate_code():
    digits = string.digits
    code = ''.join(random.sample(digits, 6))
    return code
