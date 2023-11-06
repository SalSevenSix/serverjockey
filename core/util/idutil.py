import random
# ALLOW util.dtutil
from core.util import dtutil

_BASE62_CHARS = 'Il1O0ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'


def generate_token(length: int, readable: bool = False) -> str:
    begin = 5 if readable else 0
    end = len(_BASE62_CHARS)
    result = []
    for i in range(length):
        result.append(_BASE62_CHARS[random.randrange(begin, end)])
    return ''.join(result)


def generate_id() -> str:
    return generate_token(6) + str(dtutil.now_millis())
