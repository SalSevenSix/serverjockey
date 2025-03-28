import sys
import asyncio
import time
import itertools
import random
# ALLOW util.* msg.*
from core.util import logutil, tasks, util, io, funcutil, idutil, dtutil, pkg
from core.msg import msgabc, msgftr, msglog, msgpipe


def _make_archive_script(archive_tmp: str, unpacked_dir: str) -> str:
    return f'''import sys
import logging
import shutil
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
    shutil.make_archive('{archive_tmp}', 'zip', root_dir='{unpacked_dir}', logger=logging.getLogger())
'''


def _unpack_archive_script(archive: str, target_dir: str) -> str:
    return f'''import shutil
if __name__ == '__main__':
    shutil.unpack_archive('{archive}', '{target_dir}')
'''


async def _run_script(script_file: str, logger):
    mailer, source, stderr, stdout = logger.mailer(), logger.source(), None, None
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_file, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stderr = msgpipe.PipeOutLineProducer(mailer, source, msglog.ERROR, process.stderr)
        stdout = msgpipe.PipeOutLineProducer(mailer, source, msglog.INFO, process.stdout)
        rc = await process.wait()
        if rc != 0:
            raise Exception(f'Process {process} non-zero exit, rc={rc}')
    finally:
        await funcutil.silently_cleanup(stderr)
        await funcutil.silently_cleanup(stdout)


# pylint: disable=too-many-locals
async def _archive_directory(
        unpacked_dir: str, archives_dir: str, prune_hours: int = 0,
        tempdir: str = '/tmp', logger=logutil.NullLogger()) -> str | None:
    working_dir = tempdir + '/' + idutil.generate_id()
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
        now, archive_kind = time.time(), util.fname(unpacked_dir)
        archive_name = archive_kind + '-' + dtutil.format_time('%Y%m%d', now) + '-' + dtutil.format_time('%H%M%S', now)
        script_file, archive_tmp = working_dir + '/make_archive.py', working_dir + '/' + archive_name
        await io.write_file(script_file, _make_archive_script(archive_tmp, unpacked_dir))
        await _run_script(script_file, logger)
        archive_path = archives_dir + '/' + archive_name + '.zip'
        await io.move_path(archive_tmp + '.zip', archive_path)
        logger.info(f'Created {archive_path}')
        if prune_hours > 0:
            logger.info(f'Pruning archives older than {prune_hours} hours')
            prune_time = now - float(prune_hours * 60 * 60)
            files = [o for o in await io.directory_list(archives_dir) if o['type'] == 'file']
            files = [o for o in files if o['name'].startswith(archive_kind) and o['mtime'] < prune_time]
            for file in [o['name'] for o in files]:
                logger.info(f'Deleting {file}')
                await io.delete_file(archives_dir + '/' + file)
        logger.info('END Archive Directory')
        return archive_path
    except Exception as e:
        logger.error(f'ERROR archiving {unpacked_dir} {repr(e)}')
        raise e
    finally:
        await funcutil.silently_call(io.delete_directory(working_dir))


async def _unpack_directory(
        archive: str, unpack_dir: str, wipe: bool = True,
        tempdir: str = '/tmp', logger=logutil.NullLogger()):
    working_dir, target_dir = tempdir + '/' + idutil.generate_id(), None
    progress_logger = _ProgressLogger(logger)
    try:
        logger.info('START Unpack Directory')
        assert await io.file_exists(archive)
        if unpack_dir[-1] == '/':
            unpack_dir = unpack_dir[:-1]
        logger.info(f'{archive} => {unpack_dir}')
        if await io.file_size(archive) > 104857600:  # 100Mb
            progress_logger.start()
        target_dir = unpack_dir
        if wipe:
            await io.delete_directory(target_dir)
        else:
            target_dir = tempdir + '/' + idutil.generate_id()
        await io.create_directory(working_dir, target_dir)
        script_file = working_dir + '/unpack_archive.py'
        await io.write_file(script_file, _unpack_archive_script(archive, target_dir))
        await _run_script(script_file, logger)
        progress_logger.stop()
        logger.info('SET file permissions')
        await io.auto_chmod(target_dir)
        if not wipe:
            logger.info('MOVING files')
            for name in [o['name'] for o in await io.directory_list(target_dir)]:
                source_path, target_path = target_dir + '/' + name, unpack_dir + '/' + name
                await io.delete_any(target_path)
                await io.move_path(source_path, target_path)
        logger.info('END Unpack Directory')
    except Exception as e:
        logger.error(f'ERROR unpacking {archive} {repr(e)}')
        raise e
    finally:
        progress_logger.stop()
        await funcutil.silently_call(io.delete_directory(working_dir))
        if not wipe:
            await funcutil.silently_call(io.delete_directory(target_dir))


class _ProgressLogger:

    def __init__(self, logger):
        self._logger = logger
        self._running, self._task = False, None

    def start(self):
        self._running = True
        self._task = tasks.task_start(self._run(), self)

    @staticmethod
    async def _load_lines() -> tuple:
        # https://ascii-generator.site/
        lines = await pkg.pkg_load('core.msg', 'art.txt')
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


class Archiver(msgabc.AbcSubscriber):
    REQUEST = 'Archiver.Request'
    START, COMPLETE, EXCEPTION = 'Archiver.Start', 'Archiver.Complete', 'Archiver.Exception'
    FILTER_START, FILTER_DONE = msgftr.NameIs(START), msgftr.NameIn((COMPLETE, EXCEPTION))

    def __init__(self, mailer: msgabc.Mailer, tempdir: str = '/tmp'):
        super().__init__(msgftr.NameIs(Archiver.REQUEST))
        self._mailer, self._tempdir = mailer, tempdir

    async def handle(self, message):
        source, data = message.source(), message.data()
        try:
            self._mailer.post(source, Archiver.START)
            archive_file = await self._archive(source, data)
            self._mailer.post(source, Archiver.COMPLETE, archive_file, message)
        except Exception as e:
            self._mailer.post(source, Archiver.EXCEPTION, e, message)
        return None

    async def _archive(self, source, data):
        source_dir = util.get('source_dir', data)
        if source_dir is None:
            raise Exception('No source_dir')
        backups_dir = util.get('backups_dir', data)
        if backups_dir is None:
            raise Exception('No backups_dir')
        prune_hours = int(util.get('prunehours', data, 0))
        logger = msglog.LoggingPublisher(self._mailer, source)
        return await _archive_directory(source_dir, backups_dir, prune_hours, self._tempdir, logger)


class Unpacker(msgabc.AbcSubscriber):
    REQUEST = 'Unpacker.Request'
    START, COMPLETE, EXCEPTION = 'Unpacker.Start', 'Unpacker.Complete', 'Unpacker.Exception'
    FILTER_START, FILTER_DONE = msgftr.NameIs(START), msgftr.NameIn((COMPLETE, EXCEPTION))

    def __init__(self, mailer: msgabc.Mailer, tempdir: str = '/tmp'):
        super().__init__(msgftr.NameIs(Unpacker.REQUEST))
        self._mailer, self._tempdir = mailer, tempdir

    async def handle(self, message):
        source, data = message.source(), message.data()
        try:
            self._mailer.post(source, Unpacker.START)
            unpack_dir = await self._unpack(source, data)
            self._mailer.post(source, Unpacker.COMPLETE, unpack_dir, message)
        except Exception as e:
            self._mailer.post(source, Unpacker.EXCEPTION, e, message)
        return None

    async def _unpack(self, source, data):
        root_dir = util.get('root_dir', data)
        if root_dir is None or not await io.directory_exists(root_dir):
            raise Exception('No root_dir')
        backups_dir = util.get('backups_dir', data)
        if backups_dir is None or not await io.directory_exists(backups_dir):
            raise Exception('No backups_dir')
        filename = util.get('filename', data)
        if not filename:
            raise Exception('No filename')
        archive = backups_dir + ('' if filename[0] == '/' else '/') + filename
        unpack_dir = root_dir if util.get('to_root', data) else root_dir + '/' + util.fname(filename).split('-')[0]
        wipe = util.get('wipe', data, True)
        logger = msglog.LoggingPublisher(self._mailer, source)
        await _unpack_directory(archive, unpack_dir, wipe, self._tempdir, logger)
        return unpack_dir
