import typing
import asyncio
import base64
# ALLOW util.gc
from core.util import gc

_SCRIPT_SPECIALS = str.maketrans({
    '#': r'\#', '$': r'\$', '=': r'\=', '[': r'\[', ']': r'\]',
    '!': r'\!', '<': r'\<', '>': r'\>', '{': r'\{', '}': r'\}',
    ';': r'\;', '|': r'\|', '~': r'\~', '(': r'\(', ')': r'\)',
    '*': r'\*', '?': r'\?', '&': r'\&'})


def script_escape(value: str) -> str:
    if not value:
        return value
    return value.translate(_SCRIPT_SPECIALS)


def is_format(text: str) -> bool:
    open_index, close_index = text.count('{'), text.count('}')
    if open_index == 0 and close_index == 0:
        return False
    return open_index == close_index


def single(collection: typing.Optional[typing.Collection]) -> typing.Any:
    if collection is None or len(collection) == 0:
        return None
    for item in collection:
        return item


def urlsafe_b64encode(value: str) -> str:
    value = value.encode(gc.UTF_8)
    value = base64.urlsafe_b64encode(value)
    return str(value, gc.UTF_8)


def urlsafe_b64decode(value: str) -> str:
    value = base64.urlsafe_b64decode(value)
    return str(value, gc.UTF_8)


def build_url(scheme: str = gc.HTTP,
              host: str | None = 'localhost',
              port: int | None = gc.HTTP_PORT,
              path: str = '') -> str:
    parts = [scheme, '://']
    if host:
        parts.append(host)
        if (port and not (scheme == gc.HTTP and port == gc.HTTP_PORT)
                and not (scheme == gc.HTTPS and port == gc.HTTPS_PORT)):
            parts.append(':')
            parts.append(str(port))
    if path:
        if not path.startswith('/'):
            parts.append('/')
        parts.append(path)
    return ''.join(parts)


def human_file_size(value: int | None) -> str:
    if value is None:
        return ''
    if value < 1024:
        return str(value) + ' B'
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB'):
        if abs(value) < 1024.0:
            return f'{value:3.1f} {unit}'
        value /= 1024.0
    return f'{value:.1f} YiB'


def get(key: typing.Any, dictionary: dict, default: typing.Any = None) -> typing.Any:
    if dictionary and key in dictionary:
        return dictionary[key]
    return default


def filter_dict(dictionary: dict, keys: typing.Collection, none_fill: bool = False) -> dict:
    result = {}
    for key in keys:
        if key in dictionary:
            result[key] = dictionary[key]
        elif none_fill:
            result[key] = None
    return result


def unpack_dict(dictionary: dict, keys: typing.Collection | None = None) -> tuple:
    result = []
    for key in keys if keys else dictionary.keys():
        result.append(get(key, dictionary))
    return tuple(result)


def delete_dict(dictionary: dict, keys: typing.Collection) -> dict:
    result = {}
    for key, value in dictionary.items():
        if key not in keys:
            result[key] = value
    return result


def delete_dict_by_value(dictionary: dict, value: any) -> dict:
    result = {}
    for key, candidate in dictionary.items():
        if value != candidate:
            result[key] = candidate
    return result


def keyfill_dict(dictionary: dict, template: dict, deep: bool = False) -> dict:
    result, changed = {}, False
    for key, value in dictionary.items():
        result[key] = value
    for key, value in template.items():
        if key not in result:
            changed = True
            result[key] = value
        elif deep and isinstance(result[key], dict) and isinstance(value, dict):
            value_dict = keyfill_dict(result[key], value, deep)
            if value_dict is not result[key]:
                changed = True
                result[key] = value_dict
    return result if changed else dictionary


def lchop(value: str, keyword: str, strip: bool = True) -> str:
    index = value.find(keyword)
    if index == -1:
        return value
    value = value[index + len(keyword):]
    return value.strip() if strip else value


def rchop(value: str, keyword: str, strip: bool = True) -> str:
    index = value.find(keyword)
    if index == -1:
        return value
    value = value[:index]
    return value.strip() if strip else value


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


def full_path(base: str | None, path: str | None) -> str | None:
    if not path:
        return None
    if path[0] == '/':
        return path
    if base is None:
        base = ''
    if path == '.':
        path = ''
    if base and base[-1] == '/':
        base = base[:-1]
    if path.startswith('./'):
        path = path[2:]
    sep = '/' if base and path else ''
    start = '' if base and base[0] == '/' else '/'
    return start + base + sep + path


def strip_path(path: str | None) -> str | None:
    if not path:
        return path
    return path[:-1] if path[-1] == '/' else path


def fname(path: str | None) -> str | None:
    if not path:
        return path
    return path.rsplit('/', maxsplit=1)[-1]


def fext(path: str | None) -> str | None:
    if not path:
        return path
    return path.rsplit('.', maxsplit=1)[-1]


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


def extract_hostname_ips(hostnames: str | bytes | None) -> tuple:
    data = hostnames.decode() if isinstance(hostnames, bytes) else hostnames
    data, ipv4, ipv6 = data.strip() if data else None, [], []
    if not data:
        return tuple(ipv4), tuple(ipv6)
    for item in data.split():
        len_item = len(item)
        if len(item.replace('.', '')) == (len_item - 3):
            ipv4.append(item)
        elif len(item.replace(':', '')) == (len_item - 7):
            ipv6.append(item)
    return tuple(ipv4), tuple(ipv6)
