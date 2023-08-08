import logging
import typing
import asyncio
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.util import util, io, tasks
from core.msg import msgabc, msgftr
from core.context import contextsvc
from core.system import svrsvc

# TODO post messages that can be sent to console log so users know its working or not


async def initialise(context: contextsvc.Context):
    env_path = util.get('PATH', context.config('env'))
    vmtouch = await io.find_in_env_path(env_path, 'vmtouch')
    if vmtouch:
        context.register(CachLockService(vmtouch))
    else:
        logging.debug('vmtouch not installed or not in path')


def cache_path(mailer: msgabc.Mailer, source: typing.Any, path: str):
    mailer.post(source, CachLockService.CACH_PATH, {'path': path})


class CachLockService(msgabc.AbcSubscriber):
    CACH_PATH = 'CachLockService.CachePath'
    CACH_PATH_FILTER = msgftr.NameIs(CACH_PATH)

    def __init__(self, vmtouch: str):
        super().__init__(msgftr.Or(
            msgftr.IsStop(),
            svrsvc.ServerStatus.RUNNING_FALSE_FILTER,
            CachLockService.CACH_PATH_FILTER))
        self._vmtouch = vmtouch
        self._caches = []

    def handle(self, message):
        if message is msgabc.STOP or svrsvc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            for cache_lock in self._caches:
                cache_lock.stop()
            self._caches = []
            return None
        if CachLockService.CACH_PATH_FILTER.accepts(message):
            cache_lock = _CacheLock(self._vmtouch, util.get('path', message.data()))
            self._caches.append(cache_lock)
            return None
        return None


class _CacheLock:

    def __init__(self, vmtouch: str, path: str):
        self._vmtouch, self._path = vmtouch, path
        self._process: asyncio.subprocess.Process | None = None
        self._task = tasks.task_start(self._run(), 'CacheLock(' + path + ')')

    async def _run(self):
        # noinspection PyBroadException
        try:
            self._process = await asyncio.create_subprocess_exec(self._vmtouch, '-tlq', self._path)
            rc = await self._process.wait()
            logging.debug('vmtouch exit code: ' + str(rc))
        except Exception as e:
            logging.warning('Error executing vmtouch ' + repr(e))
        finally:
            tasks.task_end(self._task)

    def stop(self):
        if not self._process or self._process.returncode is not None:
            return
        # noinspection PyBroadException
        try:
            self._process.terminate()
            # TODO should wait for task to complete, kill process if needed
        except Exception as e:
            logging.warning('Error killing vmtouch ' + repr(e))
