from core.util import util
from core.msg import msgabc, msgftr, msglog
from core.proc import proch, jobh, prcext
from core.system import svrsvc, playerstore

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('INF [Steamworks.NET] GameServer.LogOn successful, SteamID='))
CONSOLE_LOG_FILTER = msgftr.Or(
    proch.ServerProcess.FILTER_ALL_LINES,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.LoggingPublisher.FILTER_ALL_LEVELS)


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(_ServerDetailsSubscriber(mailer))
    mailer.register(_PlayerEventSubscriber(mailer))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_PREFIX = 'INF Version:'
    VERSION_SUFFIX = 'Compatibility Version:'
    VERSION_FILTER = msgftr.DataMatches('.*' + VERSION_PREFIX + '.*' + VERSION_SUFFIX + '.*')
    IP_PREFIX = 'INF [EOS] Session address:'
    IP_FILTER = msgftr.DataStrContains(IP_PREFIX)
    PORT_PREFIX = 'GamePref.ConnectToServerPort ='
    PORT_FILTER = msgftr.DataStrContains(PORT_PREFIX)
    CON_PORT_PREFIX = 'GamePref.ControlPanelPort ='
    CON_PORT_FILTER = msgftr.DataStrContains(CON_PORT_PREFIX)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.IP_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _ServerDetailsSubscriber.CON_PORT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.right_chop_and_strip(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.IP_PREFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': value})
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.PORT_PREFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'port': value})
            return None
        if _ServerDetailsSubscriber.CON_PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.CON_PORT_PREFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'cport': value})
            return None
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    PREFIX = 'INF GMSG: Player \''
    JOIN_SUFFIX = '\' joined the game'
    LEAVE_SUFFIX = '\' left the game'
    JOIN_FILTER = msgftr.DataMatches('.*' + PREFIX + '.*' + JOIN_SUFFIX + '.*')
    LEAVE_FILTER = msgftr.DataMatches('.*' + PREFIX + '.*' + LEAVE_SUFFIX + '.*')

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.JOIN_FILTER, _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.PREFIX)
            value = util.right_chop_and_strip(value, _PlayerEventSubscriber.JOIN_SUFFIX)
            self._mailer.post(
                self, playerstore.PLAYER_EVENT,
                {'event': 'login', 'player': {'steamid': False, 'name': value}})
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.PREFIX)
            value = util.right_chop_and_strip(value, _PlayerEventSubscriber.LEAVE_SUFFIX)
            self._mailer.post(
                self, playerstore.PLAYER_EVENT,
                {'event': 'logout', 'player': {'steamid': False, 'name': value}})
            return None
        return None
