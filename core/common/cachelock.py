import logging
import typing
import asyncio
# ALLOW util.* msg*.* context.* http.* system.*
from core.util import io, tasks
from core.msg import msgabc, msgftr
from core.msgc import mc
from core.context import contextsvc
# TODO can move to another package now?

# vmtouch & memlock
#  https://github.com/hoytech/vmtouch/issues/18
#  https://unix.stackexchange.com/questions/366352/etc-security-limits-conf-not-applied
#  https://www.thegeekdiary.com/how-to-set-resource-limits-for-a-process-with-systemd-in-centos-rhel-7-and-8/


NOTIFICATION = 'cachelock.Notification'
FILTER_NOTIFICATIONS = msgftr.NameIs(NOTIFICATION)


async def initialise(context: contextsvc.Context):
    executable = await io.find_in_env_path(context.env('PATH'), 'vmtouch')
    if executable:
        context.register(CachLockService(context, executable))
    else:
        logging.info('vmtouch not installed or not in path')


def set_path(mailer: msgabc.Mailer, source: typing.Any, path: str):
    mailer.post(source, CachLockService.CACHE_PATH, path)


class CachLockService(msgabc.AbcSubscriber):
    CACHE_PATH = 'CachLockService.CachePath'
    CACHE_PATH_FILTER = msgftr.NameIs(CACHE_PATH)

    def __init__(self, mailer: msgabc.Mailer, executable: str):
        super().__init__(msgftr.Or(
            msgftr.IsStop(),
            mc.ServerStatus.RUNNING_FALSE_FILTER,
            mc.ServerProcess.FILTER_STATE_STARTED,
            CachLockService.CACHE_PATH_FILTER))
        self._mailer, self._executable = mailer, executable
        self._cachelock = None

    async def handle(self, message):
        if message is msgabc.STOP or mc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            if self._cachelock:
                self._cachelock.stop()
            self._cachelock = None
            return True if message is msgabc.STOP else None
        if mc.ServerProcess.FILTER_STATE_STARTED.accepts(message):
            if self._cachelock and not await self._cachelock.start():
                self._cachelock = None
            return None
        if CachLockService.CACHE_PATH_FILTER.accepts(message):
            if self._cachelock:
                self._cachelock.stop()
            self._cachelock = _CacheLock(self._mailer, self._executable, message.data())
            return None
        return None


class _CacheLock:

    def __init__(self, mailer: msgabc.Mailer, executable: str, path: str):
        self._mailer, self._executable = mailer, executable
        self._path, self._task = path, None
        self._process: asyncio.subprocess.Process | None = None

    async def start(self) -> bool:
        if self._process:
            return True
        try:
            self._process = await asyncio.create_subprocess_exec(self._executable, '-tlq', self._path)
            self._task = tasks.task_start(self._run(), 'CacheLock(' + self._path + ')')
            return True
        except Exception as e:
            e_repr = repr(e)
            self._mailer.post(self, NOTIFICATION, '[CacheLock] EXCEPTION starting ' + e_repr)
            logging.warning('Error starting vmtouch ' + e_repr)
        return False

    async def _run(self):
        try:
            self._mailer.post(self, NOTIFICATION, '[CacheLock] STARTED ' + self._path)
            rc = await self._process.wait()
            self._mailer.post(self, NOTIFICATION, '[CacheLock] STOPPED ' + self._path)
            logging.debug('vmtouch exit code: ' + str(rc))
        except Exception as e:
            e_repr = repr(e)
            self._mailer.post(self, NOTIFICATION, '[CacheLock] EXCEPTION ' + self._path + ' ' + e_repr)
            logging.warning('Error waiting vmtouch ' + e_repr)
        finally:
            tasks.task_end(self._task)

    def stop(self):
        if not self._process or self._process.returncode is not None:
            return
        try:
            self._process.terminate()
        except Exception as e:
            logging.warning('Error killing vmtouch ' + repr(e))
