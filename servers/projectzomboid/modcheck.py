import logging
import asyncio
# ALLOW core.*
from core.util import util, dtutil, tasks
from core.msg import msgabc, msgftr
from core.msgc import mc
from core.system import svrsvc
from core.proc import proch
from servers.projectzomboid import messaging as msg

# LOG : General, 1703088424868> 2,217,854> command entered via server console (System.in): "checkModsNeedUpdate"
# LOG : General, 1703088424899> 2,217,885> CheckModsNeedUpdate: Checking...
# LOG : General, 1703088424899> 2,217,885> Checking started. The answer will be written in the log file and in the chat
# LOG : General, 1703088425200> 2,218,186> CheckModsNeedUpdate: Mods need update

_CHECK_MINUTES = 'modcheck.CHECK_MINUTES'
_CHECK_MINUTES_FILTER = msgftr.NameIs(_CHECK_MINUTES)


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(_RestartSubscriber(mailer))
    mailer.register(_ModsNeedUpdateSubscriber(mailer))
    mailer.register(_CheckModsNeedUpdate(mailer))


def set_check_interval(mailer: msgabc.Mailer, source, minutes: int):
    assert isinstance(minutes, int) and minutes >= 0
    mailer.post(source, _CHECK_MINUTES, minutes)


class _CheckModsNeedUpdate(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            _CHECK_MINUTES_FILTER,
            mc.ServerProcess.FILTER_STATE_STARTED,
            mc.ServerProcess.FILTER_STATE_STOPPING,
            mc.ServerProcess.FILTER_STATES_DOWN,
            msg.SERVER_RESTART_REQUIRED_FILTER))
        self._mailer, self._seconds = mailer, 0.0
        self._checker = _CheckModsNeedUpdateTask(mailer, self._seconds)

    def handle(self, message):
        if _CHECK_MINUTES_FILTER.accepts(message):
            minutes = message.data()
            self._seconds = minutes * 60.0 if minutes > 0 else 0.0
            return None
        if mc.ServerProcess.FILTER_STATE_STARTED.accepts(message):
            self._checker.stop()
            self._checker = _CheckModsNeedUpdateTask(self._mailer, self._seconds)
            self._checker.start()
            return None
        if (mc.ServerProcess.FILTER_STATE_STOPPING.accepts(message)
                or mc.ServerProcess.FILTER_STATES_DOWN.accepts(message)
                or msg.SERVER_RESTART_REQUIRED_FILTER.accepts(message)):
            self._checker.stop()
        return None


class _CheckModsNeedUpdateTask:

    def __init__(self, mailer: msgabc.MulticastMailer, seconds: float):
        self._mailer, self._seconds = mailer, seconds
        self._queue = asyncio.Queue(maxsize=1)
        self._running, self._task = False, None

    def start(self):
        if self._running or self._seconds == 0.0:
            return
        self._running = True
        self._task = tasks.task_start(self._run(), self)

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._task and not self._task.done():
            self._queue.put_nowait(None)

    async def _run(self):
        running = True
        try:
            while running and self._running:
                running = await self._wait()
                if running and self._running:
                    await proch.PipeInLineService.request(self._mailer, self, 'checkModsNeedUpdate')
        except Exception as e:
            logging.debug('CheckModsNeedUpdateTask.run() ' + repr(e))
        finally:
            self._running = False
            util.clear_queue(self._queue)
            tasks.task_end(self._task)

    async def _wait(self) -> bool:
        try:
            await asyncio.wait_for(self._queue.get(), self._seconds)
            self._queue.task_done()
            return False
        except asyncio.TimeoutError:
            return True


class _ModsNeedUpdateSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            msg.CONSOLE_OUTPUT_FILTER,
            msgftr.DataStrContains('CheckModsNeedUpdate: Mods need update')))
        self._mailer = mailer

    def handle(self, message):
        self._mailer.post(self, msg.SERVER_RESTART_REQUIRED)
        return None


class _RestartSubscriber(msgabc.AbcSubscriber):
    WAIT = '_RestartSubscriber.Wait'
    WAIT_FILTER = msgftr.NameIs(WAIT)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            msg.SERVER_RESTART_REQUIRED_FILTER,
            _RestartSubscriber.WAIT_FILTER,
            mc.ServerProcess.FILTER_STATES_DOWN,
            msgftr.IsStop()))
        self._mailer = mailer
        self._initiated, self._second_message = 0, False

    async def handle(self, message):
        if message is msgabc.STOP or mc.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            self._initiated, self._second_message = 0, False
            return True if message is msgabc.STOP else None
        if self._initiated == 0 and msg.SERVER_RESTART_REQUIRED_FILTER.accepts(message):
            self._initiated, self._second_message = dtutil.now_millis(), False
            await proch.PipeInLineService.request(
                self._mailer, self,
                'servermsg "Mod updated. Server restart in 5 minutes. Please find a safe place and logout."')
            self._mailer.post(self, _RestartSubscriber.WAIT)
            return None
        if self._initiated > 0 and _RestartSubscriber.WAIT_FILTER.accepts(message):
            waited = dtutil.now_millis() - self._initiated
            if waited > 300000:  # 5 minutes
                self._initiated, self._second_message = 0, False
                svrsvc.ServerService.signal_restart(self._mailer, self)
                return None
            if not self._second_message and waited > 240000:  # 4 minutes
                self._second_message = True
                await proch.PipeInLineService.request(
                    self._mailer, self,
                    'servermsg "Mod updated. Server restart in 1 minute. Please find a safe place and logout."')
                self._mailer.post(self, _RestartSubscriber.WAIT)
                return None
            await asyncio.sleep(1.0)
            self._mailer.post(self, _RestartSubscriber.WAIT)
        return None
