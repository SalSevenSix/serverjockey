# ALLOW core.*
from core.util import util
from core.msg import msgabc, msgftr
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import proch
from core.common import restarts, playerstore, svrhelpers

SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('SERVER STARTED'))
CONSOLE_LOG_FILTER = mc.ServerProcess.FILTER_ALL_LINES
CONSOLE_LOG_ERROR_FILTER = msgftr.And(CONSOLE_LOG_FILTER, msgftr.DataStrStartsWith('### ERROR:'))


def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context))
    context.register(_PlayerEventSubscriber(context))
    context.register(restarts.RestartAfterWarningsSubscriber(context, _RestartWarningsBuilder(context)))
    context.register(restarts.RestartOnEmptySubscriber(context))
    context.register(_AutomaticRestartsSubscriber(context))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*versionNumber=(.*?)$')
    IP_FILTER = msgftr.DataMatches(r'^public ip: (.*?)$')
    PORT_FILTER = msgftr.DataMatches(r'^server is listening on port: (\d+)$')
    INGAMETIME_FILTER = msgftr.DataMatches(r'^### Ingametime (.*?)$')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.INGAMETIME_FILTER, _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.IP_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            ingametime = _ServerDetailsSubscriber.INGAMETIME_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ingametime=ingametime))
        elif _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            ip = _ServerDetailsSubscriber.IP_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=ip))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            port = _ServerDetailsSubscriber.PORT_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(port=port))
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    JOIN_FILTER = msgftr.DataMatches(r'^### Player (.*?) has joined the server$')
    LEAVE_FILTER = msgftr.DataMatches(r'^### Player (.*?) has left the server$')
    CHAT_FILTER = msgftr.DataMatches(r'^### Chat (.*?): (.*?)$')
    KILL_FILTER = msgftr.DataMatches(r'^### Kill (.*?)$')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER, _PlayerEventSubscriber.KILL_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER, _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.CHAT_FILTER.find_all(message.data()), 2)
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        elif _PlayerEventSubscriber.KILL_FILTER.accepts(message):
            name = _PlayerEventSubscriber.KILL_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_death(self._mailer, self, name, 'was killed by admin command')
        elif _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            name = _PlayerEventSubscriber.JOIN_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
        elif _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LEAVE_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        return None


class _AutomaticRestartsSubscriber(msgabc.AbcSubscriber):
    AFTER_WARNINGS_RESTART_FILTER = msgftr.DataStrContains('### server restart after warnings')
    ON_EMPTY_RESTART_FILTER = msgftr.DataStrContains('### server restart on empty')

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _AutomaticRestartsSubscriber.AFTER_WARNINGS_RESTART_FILTER,
                _AutomaticRestartsSubscriber.ON_EMPTY_RESTART_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _AutomaticRestartsSubscriber.AFTER_WARNINGS_RESTART_FILTER.accepts(message):
            restarts.RestartAfterWarningsSubscriber.signal_restart(self._mailer, self)
        elif _AutomaticRestartsSubscriber.ON_EMPTY_RESTART_FILTER.accepts(message):
            restarts.RestartOnEmptySubscriber.signal_restart(self._mailer, self)
        return None


class _RestartWarnings(restarts.RestartWarnings):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer, self._messages = mailer, [
            'broadcast Server restart in 10 seconds.',
            'broadcast Server restart in 30 seconds.']

    async def send_warning(self) -> float:
        if len(self._messages) == 0:
            return 0.0
        await proch.PipeInLineService.request(self._mailer, self, self._messages.pop())
        return 10.0 if len(self._messages) == 0 else 20.0


class _RestartWarningsBuilder(restarts.RestartWarningsBuilder):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def create_warninger(self) -> restarts.RestartWarnings:
        return _RestartWarnings(self._mailer)
