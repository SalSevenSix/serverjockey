import abc
import os
import shutil
import pkgutil
import time
import typing
import aiofiles
from aiofiles import os as aioos
from core.util import funcutil

DEFAULT_CHUNK_SIZE = 10240


class BytesTracker(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def processed(self, chunk: bytes):
        pass


class Readable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def read(self, length: int = -1) -> bytes:
        pass


class WrapReader(Readable):
    def __init__(self, delegate):
        self._delegate = delegate

    async def read(self, length: int = -1) -> bytes:
        return await self._delegate.read(length)


_listdir = funcutil.to_async(os.listdir)
_islinkfile = funcutil.to_async(os.path.islink)
_rmtree = funcutil.to_async(shutil.rmtree)
_pkg_load = funcutil.to_async(pkgutil.get_data)


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


async def stream_write_file(
        filename: str, stream: Readable,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        tracker: BytesTracker = None):
    async with aiofiles.open(filename, mode='wb') as file:
        await copy_bytes(stream, file, chunk_size, tracker)


async def copy_bytes(
        source: Readable, target,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        tracker: BytesTracker = None):
    pumping = True
    while pumping:
        chunk = await source.read(chunk_size)
        pumping = chunk is not None and chunk != b''
        if pumping:
            await target.write(chunk)
            if tracker:
                tracker.processed(chunk)


async def pkg_load(package: str, resource: str) -> bytes | None:
    return await _pkg_load(package, resource)
