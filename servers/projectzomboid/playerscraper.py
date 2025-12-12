import logging
import asyncio
# ALLOW core.* projectzomboid.messaging
from core.util import io, tasks, funcutil
from core.msg import msgabc, msgftr, msgpipe
from core.msgc import mc
from servers.projectzomboid import messaging as msg


def initialise(mailer: msgabc.MulticastMailer, path: str):
    mailer.register(_PlayerScraperService(mailer, path))


# [12-12-25 15:07:24.295] LOG  : ...,994> connection: guid=139611748326525797 [fully-connected] "".
class _PlayerScraperService(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer, path: str):
        super().__init__(msgftr.Or(
            msgftr.IsStop(), mc.ServerStatus.RUNNING_FALSE_FILTER,
            msgftr.And(msg.CONSOLE_OUTPUT_FILTER, msgftr.DataStrContains('[fully-connected]'))))
        self._mailer, self._path = mailer, path
        self._publisher = None

    async def handle(self, message):
        if message is msgabc.STOP or mc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            if self._publisher:
                self._publisher.stop()
            self._publisher = None
            return True if message is msgabc.STOP else None
        if not self._publisher:
            player_log = await _find_player_log(self._path)
            if not player_log:
                return None
            publisher = _PlayerScraperPublisher(self._mailer, player_log)
            if await publisher.start():
                self._publisher = publisher
        return None


class _PlayerScraperPublisher:

    def __init__(self, mailer: msgabc.Mailer, path: str):
        self._mailer, self._path = mailer, path
        self._task, self._stdout = None, None
        self._process: asyncio.subprocess.Process | None = None

    async def start(self) -> bool:
        try:
            self._process = await asyncio.create_subprocess_exec(
                'tail', '-f', self._path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            self._stdout = msgpipe.PipeOutLineProducer(
                self._mailer, self, mc.ServerProcess.STDOUT_LINE, self._process.stdout)
            self._task = tasks.task_start(self._run(), 'PlayerScraperPublisher(' + self._path + ')')
            return True
        except Exception as e:
            logging.warning('Error starting tail -f %s %s', self._path, repr(e))
        return False

    async def _run(self):
        try:
            rc = await self._process.wait()
            logging.debug('tail -f %s exit code: %s', self._path, rc)
        except Exception as e:
            logging.warning('Error waiting tail -f %s %s', self._path, repr(e))
        finally:
            await funcutil.silently_cleanup(self._stdout)
            tasks.task_end(self._task)

    def stop(self):
        if not self._process or self._process.returncode is not None:
            return
        try:
            self._process.terminate()
        except Exception as e:
            logging.warning('Error killing tail -f %s %s', self._path, repr(e))


async def _find_player_log(path: str) -> str | None:
    try:
        files = await io.directory_list(path)
        files = [o for o in files if o['type'] == 'file' and o['name'].endswith('_user.txt')]
        latest = dict(name='', mtime=0.0)
        for current in files:
            if current['mtime'] > latest['mtime']:
                latest = current
        return path + '/' + latest['name'] if latest['name'] else None
    except Exception as e:
        logging.warning('Error find_player_log(%s) %s', path, repr(e))
    return None
