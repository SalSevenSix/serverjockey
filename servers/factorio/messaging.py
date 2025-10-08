# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import playerstore, rconsvc, svrhelpers

SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataMatches(
        '.*Info CommandLineMultiplayer.*Maximum segment size.*maximum-segment-size.*minimum-segment-size.*'))
DEPLOYMENT_START, DEPLOYMENT_DONE = 'Deployment.Start', 'Deployment.Done'
FILTER_DEPLOYMENT_START, FILTER_DEPLOYMENT_DONE = msgftr.NameIs(DEPLOYMENT_START), msgftr.NameIs(DEPLOYMENT_DONE)
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES, rconsvc.RconService.FILTER_OUTPUT,
    jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, msgftr.DataMatches(r'^\d*\.\d* Error .*'))


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state(FILTER_DEPLOYMENT_START, FILTER_DEPLOYMENT_DONE).init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.local_ip()))
    context.register(_PlayerEventSubscriber(context))


# 0.000 2025-10-07 08:22:06; Factorio 2.0.60 (build 83512, linux64, headless, space-age)
# 2.421 Hosting game at IP ADDR:({0.0.0.0:34197})
# 3.804 Info ServerRouter.cpp:547: Own address is IP ADDR:({14.237.58.218:34197}) (confirmed by pingpong2)
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*Factorio (.*?) \(build.*headless.*')
    PORT_FILTER = msgftr.DataMatches(r'.*Hosting game at IP ADDR:\(\{(.*?):(.*?)\}\)$')
    IP_FILTER = msgftr.DataMatches(r'.*Info.*Own address is IP ADDR:\(\{(.*?):.*\}\).*confirmed by pingpong.*')

    def __init__(self, mailer: msgabc.Mailer, local_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _ServerDetailsSubscriber.IP_FILTER)))
        self._mailer, self._local_ip = mailer, local_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            ip, port = util.fill(_ServerDetailsSubscriber.PORT_FILTER.find_all(message.data()), 2)
            ip = self._local_ip if ip == '0.0.0.0' else ip
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=ip, port=port))
        elif _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            ip = _ServerDetailsSubscriber.IP_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=ip))
        return None


# 2025-10-08 08:58:34 [JOIN] bsalis joined the game
# 2025-10-08 08:58:52 [CHAT] bsalis: hello everyone
# 2025-10-08 08:58:55 [LEAVE] bsalis left the game
# 2025-10-08 09:02:35 [KICK] bsalis was kicked by <server>. Reason: He is a meany.
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    JOIN_FILTER = msgftr.DataMatches(r'.*\[JOIN\] (.*?) joined the game$')
    CHAT_FILTER = msgftr.DataMatches(r'.*\[CHAT\] (.*?): (.*?)$')
    LEAVE_FILTER = msgftr.DataMatches(r'.*\[LEAVE\] (.*?) left the game$')
    KICK_FILTER = msgftr.DataMatches(r'.*\[KICK\] (.*?) was kicked.*')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.LEAVE_FILTER,
                      _PlayerEventSubscriber.KICK_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.CHAT_FILTER.find_all(message.data()), 2)
            if name == '<server>' and text and text.startswith('@'):
                return None  # Ignore chat messages from /console/say command
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
            return None
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            name = _PlayerEventSubscriber.JOIN_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
        elif _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LEAVE_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        elif _PlayerEventSubscriber.KICK_FILTER.accepts(message):
            name = _PlayerEventSubscriber.KICK_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        return None
