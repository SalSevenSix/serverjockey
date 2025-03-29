import sys
import asyncio
import time
import itertools
import random
# ALLOW util.* msg.*
from core.util import tasks, util, io, funcutil, idutil, dtutil, pkg
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


async def _run_script(logger: msglog.LogPublisher, script_file: str):
    mailer, source, name = logger.mailer(), logger.source(), logger.name()
    stderr, stdout = None, None
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_file, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stderr = msgpipe.PipeOutLineProducer(mailer, source, name, process.stderr)
        stdout = msgpipe.PipeOutLineProducer(mailer, source, name, process.stdout)
        rc = await process.wait()
        if rc != 0:
            raise Exception(f'Process {process} non-zero exit, rc={rc}')
    finally:
        await funcutil.silently_cleanup(stderr)
        await funcutil.silently_cleanup(stdout)


async def _prune_archives(logger: msglog.LogPublisher, now: float, prune_hours: int,
                          archive_kind: str, archives_dir: str):
    if prune_hours == 0:
        return
    logger.log(f'Pruning archives older than {prune_hours} hours')
    prune_time = now - float(prune_hours * 60 * 60)
    files = [o for o in await io.directory_list(archives_dir) if o['type'] == 'file']
    files = [o for o in files if o['name'].startswith(archive_kind) and o['mtime'] < prune_time]
    for file in [o['name'] for o in files]:
        logger.log(f'Deleting {file}')
        await io.delete_file(archives_dir + '/' + file)


async def _archive_directory(logger: msglog.LogPublisher, unpacked_dir: str, archives_dir: str,
                             prune_hours: int = 0, tempdir: str = '/tmp') -> str | None:
    unpacked_dir, archives_dir = util.strip_path(unpacked_dir), util.strip_path(archives_dir)
    now, archive_kind = time.time(), util.fname(unpacked_dir)
    archive_name = archive_kind + '-' + dtutil.format_time('%Y%m%d', now) + '-' + dtutil.format_time('%H%M%S', now)
    working_dir, archive_path = tempdir + '/' + idutil.generate_id(), archives_dir + '/' + archive_name + '.zip'
    script_file, archive_tmp = working_dir + '/make_archive.py', working_dir + '/' + archive_name
    try:
        if not await io.directory_exists(unpacked_dir):
            logger.log('WARNING No directory to archive')
            return None
        logger.log('START Archive Directory')
        assert await io.directory_exists(archives_dir)
        await io.create_directory(working_dir)
        await io.write_file(script_file, _make_archive_script(archive_tmp, unpacked_dir))
        await _run_script(logger, script_file)
        await io.move_path(archive_tmp + '.zip', archive_path)
        logger.log(f'Created {archive_path}')
        await _prune_archives(logger, now, prune_hours, archive_kind, archives_dir)
        logger.log('END Archive Directory')
        return archive_path
    except Exception as e:
        logger.log(f'ERROR archiving {unpacked_dir} {repr(e)}')
        raise e
    finally:
        await funcutil.silently_call(io.delete_directory(working_dir))


async def _unpack_directory(logger: msglog.LogPublisher, archive: str, unpack_dir: str,
                            wipe: bool = True, tempdir: str = '/tmp'):
    progress_logger, unpack_dir = _ProgressLogger(logger), util.strip_path(unpack_dir)
    working_dir, target_dir = tempdir + '/' + idutil.generate_id(), unpack_dir
    script_file = working_dir + '/unpack_archive.py'
    try:
        logger.log('START Unpack Directory')
        assert await io.file_exists(archive)
        logger.log(f'{archive} => {unpack_dir}')
        if await io.file_size(archive) > 104857600:  # 100Mb
            progress_logger.start()
        if wipe:
            await io.delete_directory(target_dir)
        else:
            target_dir = tempdir + '/' + idutil.generate_id()
        await io.create_directory(working_dir, target_dir)
        await io.write_file(script_file, _unpack_archive_script(archive, target_dir))
        await _run_script(logger, script_file)
        progress_logger.stop()
        logger.log('SET file permissions')
        await io.auto_chmod(target_dir)
        if not wipe:
            logger.log('MOVING files')
            await io.move_directory(target_dir, unpack_dir)
        logger.log('END Unpack Directory')
    except Exception as e:
        logger.log(f'ERROR unpacking {archive} {repr(e)}')
        raise e
    finally:
        progress_logger.stop()
        await funcutil.silently_call(io.delete_directory(working_dir))
        if not wipe:
            await funcutil.silently_call(io.delete_directory(target_dir))


class _ProgressLogger:

    def __init__(self, logger: msglog.LogPublisher):
        self._logger, self._running, self._task = logger, False, None

    def start(self):
        self._running = True
        self._task = tasks.task_start(self._run(), self)

    def stop(self):
        self._running = False

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
            self._logger.log('unpacking... enjoy some ascii art while you wait!')
            lines = await _ProgressLogger._load_lines()
            index, end = 0, len(lines) - 1
            while self._running:
                self._logger.log(lines[index])
                await asyncio.sleep(1.0)
                index = index + 1 if index < end else 0
        finally:
            tasks.task_end(self._task)


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
        assert prune_hours >= 0
        logger = msglog.LogPublisher(self._mailer, source)
        return await _archive_directory(logger, source_dir, backups_dir, prune_hours, self._tempdir)


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
        logger = msglog.LogPublisher(self._mailer, source)
        await _unpack_directory(logger, archive, unpack_dir, wipe, self._tempdir)
        return unpack_dir
