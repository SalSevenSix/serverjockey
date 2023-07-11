import shutil
import lzma
import tarfile
import gzip
import time
# ALLOW util.*
from core.util import util, funcutil, io, logutil

_make_archive = funcutil.to_async(shutil.make_archive)
_unpack_archive = funcutil.to_async(shutil.unpack_archive)
_gzip_compress = funcutil.to_async(gzip.compress)
_gzip_decompress = funcutil.to_async(gzip.decompress)


async def archive_directory(unpacked_dir: str, archives_dir: str,
                            prune_hours: int = 0, logger=logutil.NullLogger()) -> str | None:
    working_dir = '/tmp/' + util.generate_id()
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


async def unpack_directory(archive: str, unpack_dir: str, wipe: bool = True, logger=logutil.NullLogger()):
    working_dir = None
    try:
        logger.info('START Unpack Directory')
        assert await io.file_exists(archive)
        logger.info(archive + ' => ' + unpack_dir)
        logger.info('No progress updates on unpacking, please be patient...')
        if unpack_dir[-1] == '/':
            unpack_dir = unpack_dir[:-1]
        working_dir = unpack_dir
        if wipe:
            await io.delete_directory(working_dir)
        else:
            working_dir = '/tmp/' + util.generate_id()
        await io.create_directory(working_dir)
        await _unpack_archive(archive, working_dir)
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
