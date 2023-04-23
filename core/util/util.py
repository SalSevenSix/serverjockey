import logging
import asyncio
import random
import base64
import json
import time
import typing
# ALLOW NONE

_BASE62_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
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


def generate_token(length: int) -> str:
    result = []
    for i in range(length):
        result.append(_BASE62_CHARS[random.randrange(0, 61)])
    return ''.join(result)


def is_format(text: str) -> bool:
    open_index, close_index = text.count('{'), text.count('}')
    if open_index == 0 and close_index == 0:
        return False
    return open_index == close_index


def to_millis(value: float) -> int:
    return int(value * 1000.0) + 1


def now_millis() -> int:
    return to_millis(time.time())


def single(collection: typing.Optional[typing.Collection]) -> typing.Any:
    if collection is None or len(collection) == 0:
        return None
    for item in collection:
        return item


def obj_to_str(obj: typing.Any) -> str:
    value = repr(obj)
    if obj is None or isinstance(obj, (str, tuple, list, dict, bool, int, float)):
        return value
    result = value.replace(' object at ', ':')
    if result == value:
        return result
    return result[:-1].split('.')[-1]


def obj_to_dict(obj: typing.Any) -> typing.Optional[dict]:
    if obj is None or isinstance(obj, dict):
        return obj
    if hasattr(obj, 'asdict'):
        return obj.asdict()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise Exception('obj_to_dict() failed converting {} to dict'.format(obj))


def obj_to_json(obj: typing.Any, pretty: bool = False) -> typing.Optional[str]:
    if obj is None:
        return None
    encoder = None if isinstance(obj, dict) else _JsonEncoder
    if hasattr(obj, '__dict__'):
        obj = obj.__dict__
    try:
        if pretty:
            return json.dumps(obj, cls=encoder, indent=2, separators=(',', ': '))
        return json.dumps(obj, cls=encoder)
    except Exception as e:
        logging.warning('Not serializable to JSON. raised: %s', repr(e))
        return None


def json_to_dict(text: str) -> typing.Optional[dict]:
    try:
        return json.loads(text)
    except Exception as e:
        logging.warning('Text is not valid JSON. raised: %s', repr(e))
        return None


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


def get(key: typing.Any, dictionary: dict, default: typing.Any = None):
    if key and dictionary and key in dictionary:
        return dictionary[key]
    return default


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


class _JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None or type(obj) in (str, tuple, list, dict):
            return obj
        return obj_to_str(obj)
