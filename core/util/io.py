import abc
import typing
import os
import shutil
import pathlib
import aiofiles
from aiofiles import os as aioos
# ALLOW util.*
from core.util import util, dtutil, idutil, funcutil, objconv

DEFAULT_CHUNK_SIZE = 65536  # 64Kb


class BytesTracker(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def processed(self, chunk: bytes | None):
        pass


class NullBytesTracker(BytesTracker):

    def processed(self, chunk: bytes | None):
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


_is_symlink = funcutil.to_async(os.path.islink)
_move = funcutil.to_async(shutil.move)
_rmtree = funcutil.to_async(shutil.rmtree)


def _touch_file(filename: str):
    pathlib.Path(filename).touch()


def _find_files(path: str, search: str) -> tuple:
    result = []
    for current_dir_path, subdir_names, file_names in os.walk(path):
        for file_name in file_names:
            if search == file_name:
                result.append(os.path.join(current_dir_path, file_name))
    return tuple(result)


def _auto_chmod(path: str):
    for current_dir_path, subdir_names, file_names in os.walk(path):
        for file_name in file_names:
            if file_name.find('.') == -1 or file_name.endswith('.sh') or file_name.endswith('.x86_64'):
                file_path = os.path.join(current_dir_path, file_name)
                os.chmod(file_path, 0o774)


touch_file = funcutil.to_async(_touch_file)
find_files = funcutil.to_async(_find_files)
auto_chmod = funcutil.to_async(_auto_chmod)
chmod = funcutil.to_async(os.chmod)


def end_of_stream(chunk: bytes | None):
    return chunk is None or chunk == b''


async def directory_exists(path: typing.Optional[str]) -> bool:
    if path is None:
        return False
    return await aioos.path.isdir(path)


async def file_exists(path: typing.Optional[str]) -> bool:
    if path is None:
        return False
    return await aioos.path.isfile(path)


async def symlink_exists(path: typing.Optional[str]) -> bool:
    if path is None:
        return False
    return await _is_symlink(path)


async def create_directory(*paths: str):
    for path in paths:
        if not await directory_exists(path):
            await aioos.mkdir(path)


async def create_directories(path: str):
    current = ''
    for part in path.split('/'):
        if part:
            current += '/' + part
            await create_directory(current)


async def create_symlink(symlink_path: str, target_path: str):
    await delete_any(symlink_path)
    await aioos.symlink(target_path, symlink_path)


async def rename_path(source: str, target: str):
    await aioos.rename(source, target)


async def move_path(source: str, target: str):
    await _move(source, target)


async def delete_directory(path: str):
    if await directory_exists(path):
        await _rmtree(path)


async def delete_file(file: str):
    if await file_exists(file) or await symlink_exists(file):
        await aioos.remove(file)


async def delete_any(path: str):
    if await directory_exists(path):
        await _rmtree(path)
    else:
        await delete_file(path)


async def find_in_env_path(env_path: str | None, executable: str) -> str | None:
    if env_path is None:
        return None
    for path in env_path.split(':'):
        filename = path + '/' + executable
        if await file_exists(filename):
            return filename
    return None


async def file_size(file: str) -> int:
    stats = await aioos.stat(file)
    return stats.st_size


async def file_mtime(file: str) -> float:
    return await aioos.path.getmtime(file)


async def directory_list(path: str, baseurl: str = None) -> typing.List[typing.Dict[str, typing.Union[str, float]]]:
    if not path.endswith('/'):
        path += '/'
    result = []
    for name in await aioos.listdir(path):
        exists, file, ftype, size, updated, mtime = False, path + name, 'unknown', -1, '', -1.0
        if await _is_symlink(file):
            ftype = 'link'
            if await aioos.path.isfile(file):
                exists, size = True, await file_size(file)
            elif await aioos.path.isdir(file):
                exists = True
        elif await aioos.path.isfile(file):
            exists, ftype, size = True, 'file', await file_size(file)
        elif await aioos.path.isdir(file):
            exists, ftype = True, 'directory'
        if exists:
            mtime = await file_mtime(file)
            updated = dtutil.format_time_standard(mtime)
        entry = {'type': ftype, 'name': name, 'updated': updated, 'mtime': mtime}
        if size > -1:
            entry['size'] = size
        if baseurl:
            entry['url'] = baseurl + '/' + name
        result.append(entry)
    return result


async def move_directory(source: str, target: str):
    for name in [o['name'] for o in await directory_list(source)]:
        source_path, target_path = source + '/' + name, target + '/' + name
        await delete_any(target_path)
        await move_path(source_path, target_path)


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


async def stream_copy_file(
        from_path: str, to_path: str, chunk_size: int = DEFAULT_CHUNK_SIZE,
        tempdir: str = '/tmp', tracker: BytesTracker = NullBytesTracker()):
    async with aiofiles.open(from_path, mode='rb') as file:
        await stream_write_file(to_path, WrapReader(file), chunk_size, tempdir, tracker)


async def stream_write_file(
        filename: str, stream: Readable, chunk_size: int = DEFAULT_CHUNK_SIZE,
        tempdir: str = '/tmp', tracker: BytesTracker = NullBytesTracker()):
    working_dir = tempdir + '/' + idutil.generate_id()
    try:
        await create_directory(working_dir)
        tempfile = working_dir + '/' + util.fname(filename)
        async with aiofiles.open(tempfile, mode='wb') as file:
            await copy_bytes(stream, file, chunk_size, tracker)
        await delete_file(filename)
        await move_path(tempfile, filename)
    finally:
        await funcutil.silently_call(delete_directory(working_dir))


async def copy_bytes(
        source: Readable, target,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        tracker: BytesTracker = NullBytesTracker()):
    try:
        pumping = True
        while pumping:
            chunk = await source.read(chunk_size)
            pumping = not end_of_stream(chunk)
            if pumping:
                await target.write(chunk)
                tracker.processed(chunk)
    finally:
        tracker.processed(None)


async def keyfill_json_file(filename: str, template: dict, preprocessor: callable = None) -> bool:
    if await file_exists(filename):
        original = objconv.json_to_dict(await read_file(filename))
        loaded = preprocessor(original) if preprocessor else original
        filled = util.keyfill_dict(loaded, template, True)
        updated = (loaded is not original) or (filled is not loaded)
        if updated:
            await write_file(filename, objconv.obj_to_json(filled, pretty=True))
    else:
        updated = True
        await write_file(filename, objconv.obj_to_json(template, pretty=True))
    return updated
