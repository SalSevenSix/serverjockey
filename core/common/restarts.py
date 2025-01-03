import typing
import abc
import asyncio
# ALLOW util.* msg*.* context.* http.* system.* proc.*
from core.msg import msgabc, msgftr
from core.msgc import mc, sc
from core.system import svrsvc


class RestartWarnings(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def send_warning(self) -> float:  # return seconds to next warning or 0 to restart
        pass


class RestartWarningsBuilder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_warninger(self) -> RestartWarnings:
        pass


class RestartAfterWarningsSubscriber(msgabc.AbcSubscriber):
    _RESTART, _WAIT = 'RestartAfterWarningsSubscriber.Restart', 'RestartAfterWarningsSubscriber.Wait'
    _RESTART_FILTER, _WAIT_FILTER = msgftr.NameIs(_RESTART), msgftr.NameIs(_WAIT)

    @staticmethod
    def signal_restart(mailer: msgabc.Mailer, source: any, warninger: RestartWarnings = None):
        mailer.post(source, RestartAfterWarningsSubscriber._RESTART, warninger)

    def __init__(self, mailer: msgabc.MulticastMailer, warninger_builder: RestartWarningsBuilder = None):
        super().__init__(msgftr.Or(
            RestartAfterWarningsSubscriber._RESTART_FILTER, RestartAfterWarningsSubscriber._WAIT_FILTER,
            mc.ServerProcess.FILTER_STATES_DOWN, msgftr.IsStop()))
        self._mailer, self._warninger_builder = mailer, warninger_builder
        self._next_warning, self._warninger = None, None

    async def handle(self, message):
        if message is msgabc.STOP or mc.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            self._next_warning, self._warninger = None, None
            return True if message is msgabc.STOP else None
        if self._next_warning is None:
            if RestartAfterWarningsSubscriber._RESTART_FILTER.accepts(message):
                status = await svrsvc.ServerStatus.get_status(self._mailer, self)
                if status['state'] != sc.STARTED:
                    return None
                warninger = message.data()
                if not warninger and self._warninger_builder:
                    warninger = self._warninger_builder.create_warninger()
                if not warninger:
                    return None  # silently fail
                wait_warning = await warninger.send_warning()
                if wait_warning > 0.0:
                    self._next_warning, self._warninger = message.created() + wait_warning, warninger
                    self._mailer.post(self, RestartAfterWarningsSubscriber._WAIT)
                else:
                    svrsvc.ServerService.signal_restart(self._mailer, self)
            return None
        if RestartAfterWarningsSubscriber._WAIT_FILTER.accepts(message):
            if message.created() > self._next_warning:
                wait_warning = await self._warninger.send_warning()
                if wait_warning > 0.0:
                    self._next_warning = message.created() + wait_warning
                    self._mailer.post(self, RestartAfterWarningsSubscriber._WAIT)
                else:
                    self._next_warning, self._warninger = None, None
                    svrsvc.ServerService.signal_restart(self._mailer, self)
                return None
            await asyncio.sleep(1.0)
            self._mailer.post(self, RestartAfterWarningsSubscriber._WAIT)
        return None


class RestartOnEmptySubscriber(msgabc.AbcSubscriber):
    _RESTART = 'RestartOnEmptySubscriber.Restart'
    _RESTART_FILTER = msgftr.NameIs(_RESTART)

    @staticmethod
    def signal_restart(mailer: msgabc.Mailer, source: any):
        mailer.post(source, RestartOnEmptySubscriber._RESTART)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(mc.PlayerStore.EVENT_FILTER, RestartOnEmptySubscriber._RESTART_FILTER))
        self._mailer = mailer
        self._player_names, self._waiting = set(), False

    async def handle(self, message):
        if RestartOnEmptySubscriber._RESTART_FILTER.accepts(message):
            if not self._waiting:
                status = await svrsvc.ServerStatus.get_status(self._mailer, self)
                if status['state'] == sc.STARTED:
                    if len(self._player_names) == 0:
                        svrsvc.ServerService.signal_restart(self._mailer, self)
                    else:
                        self._waiting = True
            return None
        data = message.data().asdict()
        event_name = data['event']
        if event_name == sc.CLEAR:
            self._player_names, self._waiting = set(), False
            return None  # no restart because CLEAR does not mean last player logged out
        player_name = data['player']['name']
        if event_name == sc.LOGIN:
            self._player_names.add(player_name)
        elif event_name == sc.LOGOUT:
            if player_name in self._player_names:
                self._player_names.remove(player_name)
                if self._waiting and len(self._player_names) == 0:
                    self._player_names, self._waiting = set(), False
                    svrsvc.ServerService.signal_restart(self._mailer, self)
        return None


COMMANDS: typing.Dict[str, typing.Callable] = {
    'restart-after-warnings': RestartAfterWarningsSubscriber.signal_restart,
    'restart-on-empty': RestartOnEmptySubscriber.signal_restart}
