# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import playerstore, rconsvc, svrhelpers


_SERVER_VERSION_KEY = 'Game version is'
_SERVER_VERSION_FILTER = msgftr.DataStrStartsWith(_SERVER_VERSION_KEY)
SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, _SERVER_VERSION_FILTER)
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES, rconsvc.RconService.FILTER_OUTPUT,
    jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))


# Game version is v0.3.10.61027
# Running Palworld dedicated server on :8211
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    PORT_FILTER = msgftr.DataStrStartsWith('Running Palworld dedicated server on')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_ALL_LINES,
            msgftr.Or(_SERVER_VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        if _SERVER_VERSION_FILTER.accepts(message):
            version = util.lchop(message.data(), _SERVER_VERSION_KEY)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            port = util.lchop(message.data(), ':')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=port))
        return None


# [2026-08-02 13:41:39] [LOG] Apollo 192.168.1.7 connected the server. (User id: steam_76735473254754543)
# [2026-08-02 13:42:08] [LOG] Apollo joined the server. (User id: steam_76735473254754543, Player id: D74EBDB1000000)
# [2026-08-02 13:43:28] [CHAT] <Apollo> hello from game
# [2026-08-02 13:43:58] [LOG] Apollo left the server. (User id: steam_76735473254754543)
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    JOIN_FILTER = msgftr.DataMatches(r'^\[.*\] \[LOG\] (.*?) joined the server. \(User.*')
    CHAT_FILTER = msgftr.DataMatches(r'^\[.*\] \[CHAT\] <(.*?)> (.*?)$')
    LEFT_FILTER = msgftr.DataMatches(r'^\[.*\] \[LOG\] (.*?) left the server. \(User.*')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.LEFT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.CHAT_FILTER.find_all(message.data()), 2)
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        elif _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            name = _PlayerEventSubscriber.JOIN_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
        elif _PlayerEventSubscriber.LEFT_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LEFT_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        return None
