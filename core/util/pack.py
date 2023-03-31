import shutil
import lzma
import tarfile
import gzip
import time
from core.util import funcutil, io, logutil

_make_archive = funcutil.to_async(shutil.make_archive)
_unpack_archive = funcutil.to_async(shutil.unpack_archive)
_gzip_compress = funcutil.to_async(gzip.compress)
_gzip_decompress = funcutil.to_async(gzip.decompress)


async def archive_directory(unpacked_dir: str, archives_dir: str,
                            prune_hours: int = 0, logger=logutil.NullLogger()) -> str | None:
    if unpacked_dir[-1] == '/':
        unpacked_dir = unpacked_dir[:-1]
    if not await io.directory_exists(unpacked_dir):
        logger.info('WARNING No directory to archive')
        logger.info('END Archive Directory')
        return None
    if archives_dir[-1] == '/':
        archives_dir = archives_dir[:-1]
    assert await io.directory_exists(archives_dir)
    archive_kind = unpacked_dir.split('/')[-1]
    archive, now = archives_dir + '/' + archive_kind, time.time()
    local_now = time.localtime(now)
    archive += '-' + time.strftime('%Y%m%d', local_now)
    archive += '-' + time.strftime('%H%M%S', local_now)
    logger.info('START Archive Directory')
    result = await _make_archive(archive, 'zip', root_dir=unpacked_dir, logger=logger)
    logger.info('Created ' + result)
    if prune_hours > 0:
        logger.info('Pruning archived older than ' + str(prune_hours) + ' hours')
        prune_time = now - float(prune_hours * 60 * 60)
        files = [o for o in await io.directory_list_dict(archives_dir) if o['type'] == 'file']
        files = [o for o in files if o['name'].startswith(archive_kind) and o['mtime'] < prune_time]
        for file in [o['name'] for o in files]:
            logger.info('Deleting ' + file)
            await io.delete_file(archives_dir + '/' + file)
    logger.info('END Archive Directory')
    return result


async def unpack_directory(archive: str, unpack_dir: str, logger=logutil.NullLogger()):
    assert await io.file_exists(archive)
    if unpack_dir[-1] == '/':
        unpack_dir = unpack_dir[:-1]
    await io.delete_directory(unpack_dir)
    await io.create_directory(unpack_dir)
    # TODO Add filename to logging
    logger.info('START Unpack Directory')
    await _unpack_archive(archive, unpack_dir)
    logger.info('SET file permissions')
    await io.auto_chmod(unpack_dir)
    logger.info('END Unpack Directory')


async def gzip_compress(data: bytes) -> bytes:
    return await _gzip_compress(data)


async def gzip_decompress(data: bytes) -> bytes:
    return await _gzip_decompress(data)


def _unpack_tarxz(file_path: str, target_directory: str):
    with lzma.open(file_path) as fd:
        with tarfile.open(fileobj=fd) as tar:
            tar.extractall(target_directory)


unpack_tarxz = funcutil.to_async(_unpack_tarxz)
