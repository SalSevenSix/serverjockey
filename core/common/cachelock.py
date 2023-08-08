import logging
import typing
import asyncio
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.util import util, io, tasks
from core.msg import msgabc, msgftr
from core.context import contextsvc
from core.system import svrsvc

NOTIFICATION = 'cachelock.Notification'
FILTER_NOTIFICATIONS = msgftr.NameIs(NOTIFICATION)


async def initialise(context: contextsvc.Context):
    env_path = util.get('PATH', context.config('env'))
    executable = await io.find_in_env_path(env_path, 'vmtouch')
    if executable:
        context.register(CachLockService(context, executable))
    else:
        logging.debug('vmtouch not installed or not in path')


def cache_path(mailer: msgabc.Mailer, source: typing.Any, path: str):
    mailer.post(source, CachLockService.CACH_PATH, {'path': path})


class CachLockService(msgabc.AbcSubscriber):
    CACH_PATH = 'CachLockService.CachePath'
    CACH_PATH_FILTER = msgftr.NameIs(CACH_PATH)

    def __init__(self, mailer: msgabc.Mailer, executable: str):
        super().__init__(msgftr.Or(
            msgftr.IsStop(),
            svrsvc.ServerStatus.RUNNING_FALSE_FILTER,
            CachLockService.CACH_PATH_FILTER))
        self._mailer, self._executable = mailer, executable
        self._caches = []

    async def handle(self, message):
        if message is msgabc.STOP or svrsvc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            for cache_lock in self._caches:
                cache_lock.stop()
            self._caches = []
            return None
        if CachLockService.CACH_PATH_FILTER.accepts(message):
            path = util.get('path', message.data())
            cache_lock = _CacheLock(self._mailer, self._executable, path)
            if await cache_lock.start():
                self._caches.append(cache_lock)
            return None
        return None


class _CacheLock:

    def __init__(self, mailer: msgabc.Mailer, executable: str, path: str):
        self._mailer, self._executable = mailer, executable
        self._path, self._task = path, None
        self._process: asyncio.subprocess.Process | None = None

    async def start(self) -> bool:
        # noinspection PyBroadException
        try:
            self._mailer.post(self, NOTIFICATION, 'CacheLock LOCKING ' + self._path)
            self._process = await asyncio.create_subprocess_exec(self._executable, '-tlq', self._path)
            self._task = tasks.task_start(self._run(), 'CacheLock(' + self._path + ')')
            return True
        except Exception as e:
            logging.warning('Error starting vmtouch ' + repr(e))
        return False

    async def _run(self):
        # noinspection PyBroadException
        try:
            self._mailer.post(self, NOTIFICATION, 'CacheLock LOCKED ' + self._path)
            rc = await self._process.wait()
            logging.debug('vmtouch exit code: ' + str(rc))
        except Exception as e:
            logging.warning('Error waiting vmtouch ' + repr(e))
        finally:
            tasks.task_end(self._task)

    def stop(self):
        if not self._process or self._process.returncode is not None:
            return
        # noinspection PyBroadException
        try:
            self._mailer.post(self, NOTIFICATION, 'CacheLock UNLOCKED ' + self._path)
            self._process.terminate()
            # TODO should wait for task to complete, kill process if needed
        except Exception as e:
            logging.warning('Error killing vmtouch ' + repr(e))
