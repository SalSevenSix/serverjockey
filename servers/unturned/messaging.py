# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import playerstore, svrhelpers

_SPAM = r'^src/steamnetworkingsockets/clientlib/steamnetworkingsockets_lowlevel.cpp (.*) : usecElapsed >= 0$'
_STARTED_FILTER = msgftr.DataEquals('Loading level: 100%')
DEFAULT_PORT = 27015
SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, _STARTED_FILTER)
CONSOLE_LOG_FILTER = msgftr.Or(
    msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, msgftr.Not(msgftr.DataMatches(_SPAM))),
    jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, msgftr.DataStrContains(' k_EResult'))


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))


# \x1b[?1h\x1b=\x1b[6n\x1b[H\x1b[2J\x1b]0;Unturned\x07\x1b37mGame version: 3.22.19.4 Engine version: 2020.3.38f1
# [YYYY-MM-DD 01:52:46] Successfully set port to 27027!
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_PREFIX, VERSION_SUFFIX = 'Game version:', 'Engine version:'
    VERSION_FILTER = msgftr.DataMatches('.*' + VERSION_PREFIX + '.*' + VERSION_SUFFIX + '.*')
    PORT_PREFIX = 'Successfully set port to'
    PORT_FILTER = msgftr.DataStrStartsWith(PORT_PREFIX)

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _STARTED_FILTER)))
        self._mailer, self._public_ip, self._port = mailer, public_ip, DEFAULT_PORT

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.rchop(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=value))
            self._port = DEFAULT_PORT  # reset to default every start
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.PORT_PREFIX)
            self._port = value[:-1]
        elif _STARTED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=self._port))
        return None


class DeathMessageFilter(msgabc.Filter):
    def accepts(self, message):
        data = message.data()
        return data and data[-1] == '!'


# Connecting: PlayerID: 76561197968989085 Name: Apollo Character: Apollo
# Disconnecting: PlayerID: 76561197968989085 Name: Apollo Character: Apollo
# Successfully kicked Apollo!
# [World] Apollo [Apollo]: "Hello World"
# Say Hello Everyone   <-- command
# Apollo [Apollo] was mauled by a zombie!
# Apollo [Apollo] suffocated to death!
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT, NAME, CHARACTER, KICK = '[World]', 'Name:', 'Character:', 'Successfully kicked'
    CHAT_FILTER = msgftr.DataStrContains(CHAT)
    LOGIN_FILTER = msgftr.DataMatches('.*Connecting: PlayerID:.*' + NAME + '.*' + CHARACTER + '.*')
    LOGOUT_FILTER = msgftr.DataMatches('.*Disconnecting: PlayerID:.*' + NAME + '.*' + CHARACTER + '.*')
    KICK_FILTER = msgftr.DataStrStartsWith(KICK)
    DEATH_FILTER = DeathMessageFilter()

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.LOGIN_FILTER,
                      _PlayerEventSubscriber.LOGOUT_FILTER,
                      _PlayerEventSubscriber.KICK_FILTER,
                      _PlayerEventSubscriber.DEATH_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.CHAT)
            name = util.lchop(value, '[')
            name = util.rchop(name, ']')
            text = util.lchop(value, ']: "')[:-1]
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        elif _PlayerEventSubscriber.KICK_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.KICK)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value[:-1])
        elif _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.NAME)
            value = util.rchop(value, _PlayerEventSubscriber.CHARACTER)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
        elif _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.NAME)
            value = util.rchop(value, _PlayerEventSubscriber.CHARACTER)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
        elif _PlayerEventSubscriber.DEATH_FILTER.accepts(message):
            value = message.data()
            name = util.rchop(value, '[')
            prefix = name + ' [' + name + ']'
            if value != prefix and value.startswith(prefix):
                text = value[len(prefix) + 1:-1]
                playerstore.PlayersSubscriber.event_death(self._mailer, self, name, text)
        return None
