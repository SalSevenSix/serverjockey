import shutil
import lzma
import tarfile
import gzip
import asyncio
import time
import random
import itertools
# ALLOW util.*
from core.util import idutil, funcutil, io, logutil, tasks, pkg

_make_archive = funcutil.to_async(shutil.make_archive)
_unpack_archive = funcutil.to_async(shutil.unpack_archive)
_gzip_compress = funcutil.to_async(gzip.compress)
_gzip_decompress = funcutil.to_async(gzip.decompress)


async def archive_directory(
        unpacked_dir: str, archives_dir: str, prune_hours: int = 0,
        tmp_dir: str = '/tmp', logger=logutil.NullLogger()) -> str | None:
    working_dir = tmp_dir + '/' + idutil.generate_id()
    try:
        if unpacked_dir[-1] == '/':
            unpacked_dir = unpacked_dir[:-1]
        if not await io.directory_exists(unpacked_dir):
            logger.warning('WARNING No directory to archive')
            return None
        logger.info('START Archive Directory')
        if archives_dir[-1] == '/':
            archives_dir = archives_dir[:-1]
        assert await io.directory_exists(archives_dir)
        await io.create_directory(working_dir)
        now = time.time()
        lnow = time.localtime(now)
        archive_kind = unpacked_dir.split('/')[-1]
        archive_name = archive_kind + '-' + time.strftime('%Y%m%d', lnow) + '-' + time.strftime('%H%M%S', lnow)
        archive_tmp = await _make_archive(working_dir + '/' + archive_name, 'zip', root_dir=unpacked_dir, logger=logger)
        assert archive_tmp.endswith('.zip')
        archive_path = archives_dir + '/' + archive_name + '.zip'
        await io.move_path(archive_tmp, archive_path)
        logger.info('Created ' + archive_path)
        if prune_hours > 0:
            logger.info('Pruning archives older than ' + str(prune_hours) + ' hours')
            prune_time = now - float(prune_hours * 60 * 60)
            files = [o for o in await io.directory_list(archives_dir) if o['type'] == 'file']
            files = [o for o in files if o['name'].startswith(archive_kind) and o['mtime'] < prune_time]
            for file in [o['name'] for o in files]:
                logger.info('Deleting ' + file)
                await io.delete_file(archives_dir + '/' + file)
        logger.info('END Archive Directory')
        return archive_path
    except Exception as e:
        logger.error('ERROR archiving ' + unpacked_dir + ' ' + repr(e))
        raise e
    finally:
        await funcutil.silently_call(io.delete_directory(working_dir))


async def unpack_directory(
        archive: str, unpack_dir: str, wipe: bool = True,
        tmp_dir: str = '/tmp', logger=logutil.NullLogger()):
    working_dir, progress_logger = None, _ProgressLogger(logger)
    try:
        logger.info('START Unpack Directory')
        assert await io.file_exists(archive)
        if unpack_dir[-1] == '/':
            unpack_dir = unpack_dir[:-1]
        logger.info(archive + ' => ' + unpack_dir)
        if await io.file_size(archive) > 104857600:  # 100Mb
            progress_logger.start()
        working_dir = unpack_dir
        if wipe:
            await io.delete_directory(working_dir)
        else:
            working_dir = tmp_dir + '/' + idutil.generate_id()
        await io.create_directory(working_dir)
        await _unpack_archive(archive, working_dir)
        progress_logger.stop()
        logger.info('SET file permissions')
        await io.auto_chmod(working_dir)
        if not wipe:
            logger.info('MOVING files')
            for name in [o['name'] for o in await io.directory_list(working_dir)]:
                source_path, target_path = working_dir + '/' + name, unpack_dir + '/' + name
                await io.delete_any(target_path)
                await io.move_path(source_path, target_path)
        logger.info('END Unpack Directory')
    except Exception as e:
        logger.error('ERROR unpacking ' + archive + ' ' + repr(e))
        raise e
    finally:
        progress_logger.stop()
        if not wipe:
            await funcutil.silently_call(io.delete_directory(working_dir))


async def gzip_compress(data: bytes) -> bytes:
    return await _gzip_compress(data)


async def gzip_decompress(data: bytes) -> bytes:
    return await _gzip_decompress(data)


def _unpack_tarxz(file_path: str, target_directory: str):
    with lzma.open(file_path) as fd:
        with tarfile.open(fileobj=fd) as tar:
            tar.extractall(target_directory)


unpack_tarxz = funcutil.to_async(_unpack_tarxz)


class _ProgressLogger:

    def __init__(self, logger):
        self._logger = logger
        self._running, self._task = False, None

    def start(self):
        self._running = True
        self._task = tasks.task_start(self._run(), 'pack.ProgressLogger.run()')

    @staticmethod
    async def _load_lines() -> tuple:
        lines = await pkg.pkg_load('core.util', 'art.txt')
        lines = lines.decode().strip().split('\n')
        arts, current, divider = [], [], ''.join(list(itertools.repeat('_', 80)))
        for line in lines:
            if line == divider:
                if len(current) > 0:
                    arts.append(current)
                current = [line]
            else:
                current.append(line)
        arts.append(current)
        random.shuffle(arts)
        lines = []
        for art in arts:
            lines.extend(art)
        return tuple(lines)

    async def _run(self):
        try:
            self._logger.info('unpacking... enjoy some ascii art while you wait!')
            lines = await _ProgressLogger._load_lines()
            index, end = 0, len(lines) - 1
            while self._running:
                self._logger.info(lines[index])
                await asyncio.sleep(1.0)
                index = index + 1 if index < end else 0
        finally:
            tasks.task_end(self._task)

    def stop(self):
        self._running = False
