import inspect
import shutil
import psutil
import logging
import base64
import json
import time
import typing
import asyncio
from functools import partial, wraps
from collections.abc import Iterable


def to_async(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(func, *args, **kwargs))

    return run


_disk_usage = to_async(shutil.disk_usage)
_virtual_memory = to_async(psutil.virtual_memory)
_cpu_percent = to_async(psutil.cpu_percent)


class _JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None or type(obj) in (str, tuple, list, dict):
            return obj
        return obj_to_str(obj)


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


def is_format(text: str) -> bool:
    open_index = text.count('{')
    close_index = text.count('}')
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
    for message in iter(collection):
        return message


def iterable(value: typing.Any) -> bool:
    return value is not None and isinstance(value, Iterable)


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
        logging.warning('Not serializable to JSON. raised: %s', e)
        return None


def json_to_dict(text: str) -> typing.Optional[dict]:
    try:
        return json.loads(text)
    except Exception as e:
        logging.warning('Text is not valid JSON. raised: %s', e)
        return None


def callable_dict(obj: typing.Any, names: typing.Collection[str]) -> typing.Dict[str, typing.Callable]:
    result = {}
    for name in iter(names):
        if hasattr(obj, name):
            attribute = getattr(obj, name)
            if callable(attribute):
                result.update({name: attribute})
    return result


async def silently_cleanup(obj: typing.Any):
    if hasattr(obj, 'stop'):
        await silently_call(obj.stop)
    if hasattr(obj, 'close'):
        await silently_call(obj.close)
    if hasattr(obj, 'shutdown'):
        await silently_call(obj.shutdown)
    if hasattr(obj, 'cleanup'):
        await silently_call(obj.cleanup)


async def silently_call(invokable: typing.Callable):
    if not callable(invokable):
        return
    try:
        if inspect.iscoroutinefunction(invokable):
            await invokable()
        else:
            invokable()
    except Exception as e:
        logging.debug('silently_call failed: ' + repr(e))


def urlsafe_b64encode(value: str) -> str:
    value = value.encode('utf-8')
    value = base64.urlsafe_b64encode(value)
    return str(value, 'utf-8')


def urlsafe_b64decode(value: str) -> str:
    value = base64.urlsafe_b64decode(value)
    return str(value, 'utf-8')


def build_url(
        host: typing.Optional[str] = None,
        port: int = 80,
        path: typing.Optional[str] = None) -> str:
    parts = ['http://', str(host) if host else 'localhost']
    if port != 80:
        parts.append(':')
        parts.append(str(port))
    if path:
        path = str(path)
        if not path.startswith('/'):
            parts.append('/')
        parts.append(path)
    return ''.join(parts)


def get(key: typing.Any, dictionary: dict, default: typing.Any = None):
    if key and dictionary and isinstance(dictionary, dict) and key in dictionary:
        return dictionary[key]
    return default


def left_chop_and_strip(line: str, keyword: str) -> str:
    index = line.find(keyword)
    if index == -1:
        return line
    return line[index + len(keyword):].strip()


def right_chop_and_strip(line: str, keyword: str) -> str:
    index = line.find(keyword)
    if index == -1:
        return line
    return line[:index].strip()


def insert_filename_suffix(filename: str, suffix: str) -> str:
    index = filename.rfind('.')
    if index == -1 or filename.rfind('/') > index:
        return filename + suffix
    return filename[:index] + suffix + filename[index:]


def overridable_full_path(base: typing.Optional[str], path: typing.Optional[str]):
    if base is None or path is None or path[0] in ('.', '/'):
        return path
    if not base.endswith('/'):
        base += '/'
    return base + path


async def system_info() -> dict:
    disk = await _disk_usage('/')
    memory = await _virtual_memory()
    cpu = await _cpu_percent(1)
    return {
        'cpu': {
            'percent': cpu
        },
        'memory': {
            'total': memory[0],
            'used': memory[3],
            'available': memory[1],
            'free': memory[4],
            'percent': memory[2]
        },
        'disk': {
            'total': disk[0],
            'used': disk[1],
            'free': disk[2],
            'percent': round((disk[1] / disk[0]) * 100, 1)
        }
    }
