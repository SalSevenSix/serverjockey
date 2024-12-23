import logging
import asyncio
import enum
# ALLOW core.*
from core.util import util, tasks
from core.msg import msgabc, msgftr
from core.msgc import mc
from core.system import svrsvc
from core.proc import proch
from core.common import restarts
from servers.projectzomboid import messaging as msg

# LOG : General, 1703088424868> 2,217,854> command entered via server console (System.in): "checkModsNeedUpdate"
# LOG : General, 1703088424899> 2,217,885> CheckModsNeedUpdate: Checking...
# LOG : General, 1703088424899> 2,217,885> Checking started. The answer will be written in the log file and in the chat
# LOG : General, 1703088425200> 2,218,186> CheckModsNeedUpdate: Mods need update


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(restarts.RestartAfterWarningsSubscriber(mailer, _NormalRestartWarningsBuilder(mailer)))
    mailer.register(restarts.RestartOnEmptySubscriber(mailer))
    mailer.register(_HandleRestartSubscriber(mailer))
    mailer.register(_ModsNeedUpdateSubscriber(mailer))
    mailer.register(_CheckModsNeedUpdate(mailer))


def apply_config(mailer: msgabc.Mailer, source, config: dict):
    mailer.post(source, _CheckModsConfig.APPLY, _CheckModsConfig(config))


async def _servermsg(mailer: msgabc.MulticastMailer, source: any, message: str):
    await proch.PipeInLineService.request(mailer, source, 'servermsg "' + message + '"')


class _NormalRestartWarningsBuilder(restarts.RestartWarningsBuilder):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def create_warninger(self) -> restarts.RestartWarnings:
        return _RestartWarnings(
            self._mailer,
            'Server restart in 5 minutes. Please find a safe place and logout.',
            'Server restart in 1 minute. Please find a safe place and logout.')


class _ModzRestartWarningsBuilder(restarts.RestartWarningsBuilder):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def create_warninger(self) -> restarts.RestartWarnings:
        return _RestartWarnings(
            self._mailer,
            'Mod updated. Server restart in 5 minutes. Please find a safe place and logout.',
            'Mod updated. Server restart in 1 minute. Please find a safe place and logout.')


class _RestartWarnings(restarts.RestartWarnings):

    def __init__(self, mailer: msgabc.MulticastMailer, initial_message: str, final_message: str):
        self._mailer, self._messages = mailer, [final_message, initial_message]

    async def send_warning(self) -> float:
        if len(self._messages) == 0:
            return 0.0
        await _servermsg(self._mailer, self, self._messages.pop())
        return 60.0 if len(self._messages) == 0 else 240.0


class _CheckModsAction(enum.Enum):
    NOTIFY_ONLY, RESTART_ON_EMPTY, RESTART_AFTER_WARNING, RESTART_IMMEDIATELY = 1, 2, 3, 4


class _CheckModsConfig:
    APPLY = '_CheckModsConfig.Apply'
    APPLY_FILTER = msgftr.NameIs(APPLY)

    def __init__(self, config: dict):
        minutes = util.get('mod_check_minutes', config, 0)
        assert isinstance(minutes, int) and minutes >= 0
        self._seconds = minutes * 60.0 if minutes > 0 else 0.0
        action = util.get('mod_check_action', config)
        self._action = _CheckModsAction(action) if action else _CheckModsAction.RESTART_AFTER_WARNING

    def mod_check_seconds(self) -> int:
        return self._seconds

    def mod_check_action(self) -> _CheckModsAction:
        return self._action


class _CheckModsNeedUpdate(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            _CheckModsConfig.APPLY_FILTER,
            mc.ServerProcess.FILTER_STATE_STARTED,
            mc.ServerProcess.FILTER_STATE_STOPPING,
            mc.ServerProcess.FILTER_STATES_DOWN,
            msg.SERVER_RESTART_REQUIRED_FILTER))
        self._mailer, self._seconds = mailer, 0.0
        self._checker = _CheckModsNeedUpdateTask(mailer, self._seconds)

    def handle(self, message):
        if _CheckModsConfig.APPLY_FILTER.accepts(message):
            self._seconds = message.data().mod_check_seconds()
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
                running = await self._next()
                if running and self._running:
                    await proch.PipeInLineService.request(self._mailer, self, 'checkModsNeedUpdate')
        except Exception as e:
            logging.debug('CheckModsNeedUpdateTask.run() ' + repr(e))
        finally:
            self._running = False
            util.clear_queue(self._queue)
            tasks.task_end(self._task)

    async def _next(self) -> bool:
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


class _HandleRestartSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(_CheckModsConfig.APPLY_FILTER, msg.SERVER_RESTART_REQUIRED_FILTER))
        self._mailer, self._action = mailer, None
        self._wb = _ModzRestartWarningsBuilder(mailer)

    async def handle(self, message):
        if _CheckModsConfig.APPLY_FILTER.accepts(message):
            self._action = message.data().mod_check_action()
            return None
        if self._action is _CheckModsAction.NOTIFY_ONLY:
            await _servermsg(self._mailer, self, 'Mod updated. No further action.')
        elif self._action is _CheckModsAction.RESTART_ON_EMPTY:
            await _servermsg(self._mailer, self, 'Mod updated. Restarting when empty.')
            restarts.RestartOnEmptySubscriber.signal_restart(self._mailer, self)
        elif self._action is _CheckModsAction.RESTART_AFTER_WARNING:
            restarts.RestartAfterWarningsSubscriber.signal_restart(self._mailer, self, self._wb.create_warninger())
        elif self._action is _CheckModsAction.RESTART_IMMEDIATELY:
            await _servermsg(self._mailer, self, 'Mod updated. Server restarting NOW.')
            await asyncio.sleep(10.0)  # grace
            svrsvc.ServerService.signal_restart(self._mailer, self)
        return None
