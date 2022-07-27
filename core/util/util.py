import inspect
import os
import shutil
import lzma
import tarfile
import logging
import json
import time
import typing
import asyncio
import aiofiles
from aiofiles import os as aioos
from functools import partial, wraps
from collections.abc import Iterable


DEFAULT_CHUNK_SIZE = 10240


def _wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(func, *args, **kwargs))
    return run


_listdir = _wrap(os.listdir)
_islinkfile = _wrap(os.path.islink)
_rmtree = _wrap(shutil.rmtree)
_make_archive = _wrap(shutil.make_archive)
_unpack_archive = _wrap(shutil.unpack_archive)


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


async def directory_exists(path: typing.Optional[str]) -> bool:
    if path is None:
        return False
    return await aioos.path.isdir(path)


async def file_exists(path: typing.Optional[str]) -> bool:
    if path is None:
        return False
    return await aioos.path.isfile(path)


async def file_size(file: str) -> int:
    stats = await aioos.stat(file)
    return stats.st_size


async def directory_list_dict(path: str, baseurl: str = None) -> typing.List[typing.Dict[str, str]]:
    if not path.endswith('/'):
        path += '/'
    result = []
    for name in iter(await _listdir(path)):
        file, ftype, size, entry = path + name, 'unknown', -1, {}
        if await _islinkfile(file):
            ftype = 'link'
        elif await aioos.path.isfile(file):
            ftype = 'file'
            size = await file_size(file)
        elif await aioos.path.isdir(file):
            ftype = 'directory'
        updated = time.ctime(await aioos.path.getmtime(file))
        entry.update({'type': ftype, 'name': name, 'updated': updated})
        if size > -1:
            entry.update({'size': size})
        if baseurl:
            entry.update({'url': baseurl + '/' + name})
        result.append(entry)
    return result


async def archive_directory(unpacked_dir: str, archives_dir: str, logger=None) -> str:
    if unpacked_dir[-1] == '/':
        unpacked_dir = unpacked_dir[:-1]
    assert await directory_exists(unpacked_dir)
    if archives_dir[-1] == '/':
        archives_dir = archives_dir[:-1]
    assert await directory_exists(archives_dir)
    archive = archives_dir + '/' + unpacked_dir.split('/')[-1] + '-' + str(now_millis())
    if logger:
        logger.info('START Archive Directory')
    result = await _make_archive(archive, 'zip', root_dir=unpacked_dir, logger=logger)
    if logger:
        logger.info('Created ' + result)
        logger.info('END Archive Directory')
    return result


async def unpack_directory(archive: str, unpack_dir: str, logger=None):
    assert await file_exists(archive)
    if unpack_dir[-1] == '/':
        unpack_dir = unpack_dir[:-1]
    if await directory_exists(unpack_dir):
        await delete_directory(unpack_dir)
    await create_directory(unpack_dir)
    if logger:
        logger.info('START Unpack Directory')
    await _unpack_archive(archive, unpack_dir)
    if logger:
        logger.info('END Unpack Directory')


async def create_directory(path: str):
    if not await aioos.path.isdir(path):
        await aioos.mkdir(path)


async def rename_path(source: str, target: str):
    await aioos.rename(source, target)


async def delete_directory(path: str):
    if await aioos.path.isdir(path):
        await _rmtree(path)


async def delete_file(file: str):
    if await file_exists(file):
        await aioos.remove(file)


async def read_file(filename: str, text: bool = True) -> typing.Union[str, bytes]:
    # noinspection PyTypeChecker
    async with aiofiles.open(file=filename, mode='r' if text else 'rb') as file:
        return await file.read()


async def write_file(filename: str, data: typing.Union[str, bytes]):
    # noinspection PyTypeChecker
    async with aiofiles.open(filename, mode='w' if isinstance(data, str) else 'wb') as file:
        await file.write(data)


async def copy_text_file(from_path: str, to_path: str) -> int:
    data = await read_file(from_path)
    await write_file(to_path, data)
    return len(data)


# TODO no stream class defined
async def stream_write_file(filename: str, stream, chunk_size: int = DEFAULT_CHUNK_SIZE):
    async with aiofiles.open(filename, mode='wb') as file:
        await copy_bytes(stream, file, chunk_size)


async def copy_bytes(source, target, chunk_size: int = DEFAULT_CHUNK_SIZE):
    pumping = True
    while pumping:
        chunk = await source.read(chunk_size)
        pumping = chunk is not None and chunk != b''
        if pumping:
            await target.write(chunk)


def _unpack_tarxz(file_path: str, target_directory: str):
    with lzma.open(file_path) as fd:
        with tarfile.open(fileobj=fd) as tar:
            tar.extractall(target_directory)


unpack_tarxz = _wrap(_unpack_tarxz)
