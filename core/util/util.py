import asyncio
import random
import base64
import time
import typing
# ALLOW NONE

_BASE62_CHARS = 'Il1O0ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
_SCRIPT_SPECIALS = str.maketrans({
    '#': r'\#', '$': r'\$', '=': r'\=', '[': r'\[', ']': r'\]',
    '!': r'\!', '<': r'\<', '>': r'\>', '{': r'\{', '}': r'\}',
    ';': r'\;', '|': r'\|', '~': r'\~', '(': r'\(', ')': r'\)',
    '*': r'\*', '?': r'\?', '&': r'\&'
})


def script_escape(value: str) -> str:
    if not isinstance(value, str):
        return value
    return value.translate(_SCRIPT_SPECIALS)


def generate_token(length: int, readable: bool = False) -> str:
    begin = 5 if readable else 0
    end = len(_BASE62_CHARS)
    result = []
    for i in range(length):
        result.append(_BASE62_CHARS[random.randrange(begin, end)])
    return ''.join(result)


def generate_id() -> str:
    return generate_token(6) + str(now_millis())


def is_format(text: str) -> bool:
    open_index, close_index = text.count('{'), text.count('}')
    if open_index == 0 and close_index == 0:
        return False
    return open_index == close_index


def to_millis(seconds: float) -> int:
    return int(seconds * 1000.0) + 1


def now_millis() -> int:
    return to_millis(time.time())


def single(collection: typing.Optional[typing.Collection]) -> typing.Any:
    if collection is None or len(collection) == 0:
        return None
    for item in collection:
        return item


def urlsafe_b64encode(value: str) -> str:
    value = value.encode('utf-8')
    value = base64.urlsafe_b64encode(value)
    return str(value, 'utf-8')


def urlsafe_b64decode(value: str) -> str:
    value = base64.urlsafe_b64decode(value)
    return str(value, 'utf-8')


def build_url(scheme: str = 'http', host: str = 'localhost', port: int = 80, path: str = '') -> str:
    parts = [scheme, '://', host]
    if port != 80:
        parts.append(':')
        parts.append(str(port))
    if path:
        if not path.startswith('/'):
            parts.append('/')
        parts.append(path)
    return ''.join(parts)


def human_file_size(value: int | None):
    if value is None:
        return ''
    if value < 1024:
        return str(value) + ' B'
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB'):
        if abs(value) < 1024.0:
            return f'{value:3.1f} {unit}'
        value /= 1024.0
    return f'{value:.1f} YiB'


def get(key: typing.Any, dictionary: dict, default: typing.Any = None):
    if key and dictionary and key in dictionary:
        return dictionary[key]
    return default


def filter_dict(dictionary: dict, keys: typing.Collection):
    result = {}
    for key in keys:
        if key in dictionary:
            result[key] = dictionary[key]
    return result


def left_chop_and_strip(value: str, keyword: str) -> str:
    index = value.find(keyword)
    if index == -1:
        return value
    return value[index + len(keyword):].strip()


def right_chop_and_strip(value: str, keyword: str) -> str:
    index = value.find(keyword)
    if index == -1:
        return value
    return value[:index].strip()


def split_lines(text: str, lines_limit: int = 0, line_char_limit: int = 0, total_char_limit: int = 0) -> tuple | None:
    if text is None:
        return None
    if 0 < total_char_limit < len(text):
        return None
    lines = text.split('\n')
    if 0 < lines_limit < len(lines):
        return None
    if line_char_limit > 0:
        for line in lines:
            if len(line) > line_char_limit:
                return None
    return tuple(lines)


def overridable_full_path(base: typing.Optional[str], path: typing.Optional[str]):
    if base is None or path is None or path[0] in ('.', '/'):
        return path
    if not base.endswith('/'):
        base += '/'
    return base + path


def clear_queue(queue: asyncio.Queue):
    if not queue:
        return
    # noinspection PyBroadException
    try:
        while True:
            queue.get_nowait()
            queue.task_done()
    except Exception:
        pass
