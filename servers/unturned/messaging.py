# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.msgc import mc
from core.system import svrsvc, svrext
from core.proc import jobh, prcext
from core.common import playerstore

DEFAULT_PORT = 27015
_STARTED_FILTER = msgftr.DataEquals('Loading level: 100%')
_SPAM = r'^src/steamnetworkingsockets/clientlib/steamnetworkingsockets_lowlevel.cpp (.*) : usecElapsed >= 0$'

SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE,
    _STARTED_FILTER)
CONSOLE_LOG_FILTER = msgftr.Or(
    msgftr.And(
        mc.ServerProcess.FILTER_ALL_LINES,
        msgftr.Not(msgftr.DataMatches(_SPAM))),
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.DataStrContains(' k_EResult'))
MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(await _ServerDetailsSubscriber(mailer).initialise())
    mailer.register(_PlayerEventSubscriber(mailer))


# \x1b[?1h\x1b=\x1b[6n\x1b[H\x1b[2J\x1b]0;Unturned\x07\x1b37mGame version: 3.22.19.4 Engine version: 2020.3.38f1
# [2024-09-02 01:52:46] Successfully set port to 27027!
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_PREFIX, VERSION_SUFFIX = 'Game version:', 'Engine version:'
    VERSION_FILTER = msgftr.DataMatches('.*' + VERSION_PREFIX + '.*' + VERSION_SUFFIX + '.*')
    PORT_PREFIX = 'Successfully set port to'
    PORT_FILTER = msgftr.DataStrStartsWith(PORT_PREFIX)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _STARTED_FILTER)))
        self._mailer, self._ip, self._port = mailer, None, DEFAULT_PORT

    async def initialise(self) -> msgabc.Subscriber:
        self._ip = await sysutil.public_ip()
        return self

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.rchop(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            self._port = DEFAULT_PORT  # reset to default every start
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.PORT_PREFIX)
            self._port = value[:-1]
            return None
        if _STARTED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': self._ip, 'port': self._port})
            return None
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
            return None
        if _PlayerEventSubscriber.KICK_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.KICK)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value[:-1])
            return None
        if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.NAME)
            value = util.rchop(value, _PlayerEventSubscriber.CHARACTER)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.NAME)
            value = util.rchop(value, _PlayerEventSubscriber.CHARACTER)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.DEATH_FILTER.accepts(message):
            value = message.data()
            name = util.rchop(value, '[')
            prefix = name + ' [' + name + ']'
            if value != prefix and value.startswith(prefix):
                text = value[len(prefix) + 1:-1]
                playerstore.PlayersSubscriber.event_death(self._mailer, self, name, text)
            return None
        return None
