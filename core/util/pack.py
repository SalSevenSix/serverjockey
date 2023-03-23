import shutil
import lzma
import tarfile
import gzip
import time
from core.util import funcutil, io

_make_archive = funcutil.to_async(shutil.make_archive)
_unpack_archive = funcutil.to_async(shutil.unpack_archive)
_gzip_compress = funcutil.to_async(gzip.compress)
_gzip_decompress = funcutil.to_async(gzip.decompress)


async def archive_directory(unpacked_dir: str, archives_dir: str, logger=None) -> str | None:
    if unpacked_dir[-1] == '/':
        unpacked_dir = unpacked_dir[:-1]
    if not await io.directory_exists(unpacked_dir):
        if logger:
            logger.info('WARNING No directory to archive')
            logger.info('END Archive Directory')
        return None
    if archives_dir[-1] == '/':
        archives_dir = archives_dir[:-1]
    assert await io.directory_exists(archives_dir)
    archive = archives_dir + '/' + unpacked_dir.split('/')[-1]
    now = time.localtime(time.time())
    archive += '-' + time.strftime('%Y%m%d', now)
    archive += '-' + time.strftime('%H%M%S', now)
    if logger:
        logger.info('START Archive Directory')
    result = await _make_archive(archive, 'zip', root_dir=unpacked_dir, logger=logger)
    if logger:
        logger.info('Created ' + result)
        logger.info('END Archive Directory')
    return result


async def unpack_directory(archive: str, unpack_dir: str, logger=None):
    assert await io.file_exists(archive)
    if unpack_dir[-1] == '/':
        unpack_dir = unpack_dir[:-1]
    await io.delete_directory(unpack_dir)
    await io.create_directory(unpack_dir)
    # TODO Add filename to logging
    if logger:
        logger.info('START Unpack Directory')
    await _unpack_archive(archive, unpack_dir)
    if logger:
        logger.info('SET file permissions')
    await io.auto_chmod(unpack_dir)
    if logger:
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
