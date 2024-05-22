# ALLOW core.*
from core.util import util
from core.msg import msgabc, msgftr, msglog, msgext
from core.system import svrsvc, svrext
from core.proc import proch, jobh, prcext
from core.common import playerstore

_SPAM = r'^src/steamnetworkingsockets/clientlib/steamnetworkingsockets_lowlevel.cpp (.*) : usecElapsed >= 0$'

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataEquals('Loading level: 100%'))
CONSOLE_LOG_FILTER = msgftr.Or(
    msgftr.And(
        proch.ServerProcess.FILTER_ALL_LINES,
        msgftr.Not(msgftr.DataMatches(_SPAM))),
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS)
MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(_ServerDetailsSubscriber(mailer))
    mailer.register(_PlayerEventSubscriber(mailer))


# \x1b[?1h\x1b=\x1b[6n\x1b[H\x1b[2J\x1b]0;Unturned\x07\x1b[37mGame version: 3.22.19.4 Engine version: 2020.3.38f1

class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_PREFIX, VERSION_SUFFIX = 'Game version:', 'Engine version:'
    VERSION_FILTER = msgftr.DataMatches('.*' + VERSION_PREFIX + '.*' + VERSION_SUFFIX + '.*')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            _ServerDetailsSubscriber.VERSION_FILTER))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.rchop(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        return None


# Connecting: PlayerID: 76561197968989085 Name: Apollo Character: Apollo
# Disconnecting: PlayerID: 76561197968989085 Name: Apollo Character: Apollo
# Successfully kicked Apollo!
# [World] Apollo [Apollo]: "Hello World"
# Say Hello Everyone   <-- command
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT, NAME, CHARACTER, KICK = '[World]', 'Name:', 'Character:', 'Successfully kicked'
    CHAT_FILTER = msgftr.DataStrContains(CHAT)
    LOGIN_FILTER = msgftr.DataMatches('.*Connecting: PlayerID:.*' + NAME + '.*' + CHARACTER + '.*')
    LOGOUT_FILTER = msgftr.DataMatches('.*Disconnecting: PlayerID:.*' + NAME + '.*' + CHARACTER + '.*')
    KICK_FILTER = msgftr.DataStrStartsWith(KICK)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.LOGIN_FILTER,
                      _PlayerEventSubscriber.LOGOUT_FILTER,
                      _PlayerEventSubscriber.KICK_FILTER)))
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
        value = util.lchop(message.data(), _PlayerEventSubscriber.NAME)
        value = util.rchop(value, _PlayerEventSubscriber.CHARACTER)
        if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
        else:
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
        return None
