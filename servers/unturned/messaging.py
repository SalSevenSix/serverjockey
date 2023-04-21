# ALLOW core.*
from core.util import util
from core.msg import msgabc, msgftr, msglog, msgext
from core.system import svrsvc, svrext
from core.proc import proch, jobh, prcext
from core.common import playerstore

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataEquals('Loading level: 100%'))
CONSOLE_LOG_FILTER = msgftr.Or(
    proch.ServerProcess.FILTER_ALL_LINES,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.LoggingPublisher.FILTER_ALL_LEVELS)
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
    VERSION_PREFIX = 'Game version:'
    VERSION_SUFFIX = 'Engine version:'
    VERSION_FILTER = msgftr.DataMatches('.*' + VERSION_PREFIX + '.*' + VERSION_SUFFIX + '.*')

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            _ServerDetailsSubscriber.VERSION_FILTER))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.right_chop_and_strip(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        return None


# \x1b[37mConnecting: PlayerID: 76561197968989085 Name: Apollo Character: Apollo
# \x1b[37mDisconnecting: PlayerID: 76561197968989085 Name: Apollo Character: Apollo

class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    NAME = 'Name:'
    CHARACTER = 'Character:'
    LOGIN_FILTER = msgftr.DataMatches('.*Connecting: PlayerID:.*' + NAME + '.*' + CHARACTER + '.*')
    LOGOUT_FILTER = msgftr.DataMatches('.*Disconnecting: PlayerID:.*' + NAME + '.*' + CHARACTER + '.*')

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.LOGIN_FILTER, _PlayerEventSubscriber.LOGOUT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        event = 'login' if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message) else 'logout'
        value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.NAME)
        value = util.right_chop_and_strip(value, _PlayerEventSubscriber.CHARACTER)
        self._mailer.post(
            self, playerstore.PLAYER_EVENT,
            {'event': event, 'player': {'steamid': False, 'name': value}})
        return None
