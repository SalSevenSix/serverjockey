import inspect
import os
import signal
import shutil
import logging
import json
import time
import uuid
import typing
import aiofiles
from aiofiles import os as aiofilesos


_isdir = aiofilesos.wrap(os.path.isdir)
_isfile = aiofilesos.wrap(os.path.isfile)
_listdir = aiofilesos.wrap(os.listdir)
_make_archive = aiofilesos.wrap(shutil.make_archive)
_rmtree = aiofilesos.wrap(shutil.rmtree)


class _JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None or type(obj) in (str, tuple, list, dict):
            return obj
        return obj_to_str(obj)


_SCRIPT_SPECIALS = str.maketrans({
    '#':  r'\#', '$':  r'\$', '=':  r'\=', '[':  r'\[', ']':  r'\]',
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


def obj_to_json(obj: typing.Any) -> typing.Optional[str]:
    if obj is None:
        return None
    encoder = None if isinstance(obj, dict) else _JsonEncoder
    if hasattr(obj, '__dict__'):
        obj = obj.__dict__
    try:
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


def str_to_b10str(value: str) -> str:
    return ''.join([str(b).zfill(3) for b in value.encode('utf-8')])


def b10str_to_str(value: str) -> str:
    chunks = [value[b:b+3] for b in range(0, len(value), 3)]
    return bytes([int(b) for b in chunks]).decode('utf-8')


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


def generate_token() -> str:
    identity = str(uuid.uuid4())
    return identity[:6] + identity[-6:]


def insert_filename_suffix(filename: str, suffix: str) -> str:
    index = filename.rfind('.')
    if index == -1 or filename.rfind('/') > index:
        return filename + suffix
    return filename[:index] + suffix + filename[index:]


def overridable_full_path(base: typing.Optional[str], path: typing.Optional[str]):
    if base is None or path is None or path[0] in ('.', '/'):
        return path
    return base + '/' + path


async def file_exists(file: typing.Optional[str]) -> bool:
    if file is None:
        return False
    return await _isfile(file)


async def directory_list_dict(path: str) -> typing.List[typing.Dict[str, str]]:
    if not path.endswith('/'):
        path = path + '/'
    result = []
    for name in iter(await _listdir(path)):
        file = path + name
        ftype = 'unknown'
        if os.path.isfile(file):
            ftype = 'file'
        elif os.path.isdir(file):
            ftype = 'directory'
        elif os.path.islink(file):
            ftype = 'link'
        updated = time.ctime(os.path.getmtime(file))
        result.append({'type': ftype, 'name': name, 'updated': updated})
    return result


async def create_directory(path: str):
    if not await _isdir(path):
        await aiofilesos.mkdir(path)


async def archive_directory(path: str, logger=None) -> str:
    parts = path.split('/')
    if parts[-1] == '':
        del parts[-1]   # chop trailing '/'
    root_dir = '/'.join(parts)
    file = parts.copy()
    file.append('..')
    file.append(parts[-1] + '-' + str(now_millis()))
    file = '/'.join(file)
    await _make_archive(file, 'zip', root_dir=root_dir, logger=logger)
    if logger:
        logger.info('Archive created: ' + file)
    return file


async def wipe_directory(path: str):
    await delete_directory(path)
    await create_directory(path)


async def delete_directory(path: str):
    await _rmtree(path, ignore_errors=True)


async def delete_file(file: str):
    if await file_exists(file):
        await aiofilesos.remove(file)


async def read_file(filename: str, text: bool = True) -> typing.Union[str, bytes]:
    mode = 'r' if text else 'rb'
    async with aiofiles.open(filename, mode=mode) as file:
        try:
            return await file.read()
        finally:
            await silently_cleanup(file)


async def write_file(filename: str, data: typing.Union[str, bytes], text: bool = True):
    mode = 'w' if text else 'wb'
    async with aiofiles.open(filename, mode=mode) as file:
        try:
            await file.write(data)
        finally:
            await silently_cleanup(file)


async def copy_file(source_file: str, target_file: str):
    data = await read_file(source_file, text=False)
    await write_file(target_file, data, text=False)


def signal_interrupt(pid: typing.Optional[int] = None):
    if pid is None:
        pid = os.getpid()
    os.kill(pid, signal.SIGINT)
