# ALLOW core.*
from core.util import util
from core.msg import msgabc, msgftr, msglog, msgext
from core.system import svrsvc, svrext
from core.proc import proch, jobh, prcext
from core.common import playerstore

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataEquals('Connection to Steam servers successful.'))
CONSOLE_LOG_FILTER = msgftr.Or(
    proch.ServerProcess.FILTER_ALL_LINES,
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


# Log file started (file "logs/L0917010.log") (game "/home/bsalis/serverjockey/gm/runtime/garrysmod") (version "9040")
# Public IP is 117.20.112.122.
# Network: IP 127.0.1.1, mode MP, dedicated Yes, ports 27015 SV / 27005 CL

class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*Log file started \(file.*\) \(game ".*"\)$')
    IP_FILTER = msgftr.DataMatches(r'^Public IP is.*\.$')
    PORT_FILTER = msgftr.DataMatches(r'^Network: IP.*mode.*dedicated.*ports.*CL$')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.IP_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), '(version "')[:-2]
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), 'Public IP is')[:-1]
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': value})
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), ', ports')
            value = util.right_chop_and_strip(value, 'SV')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'port': value})
            return None
        return None


# Apollo: Hello from game
# say Hello from console
# Console: Hello from console

# Client "Apollo" connected (192.168.64.99:27005).
# Dropped Apollo from server (Disconnect by user.)

class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT_FILTER = msgftr.DataStrContains(': ')
    JOIN_FILTER = msgftr.DataMatches(r'^Client ".*" connected .*\.$')
    LEAVE_FILTER = msgftr.DataMatches(r'^Dropped .* from server .*\)$')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer
        self._names = set()

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name = util.right_chop_and_strip(message.data(), ':')
            if name not in self._names:
                return None
            text = util.left_chop_and_strip(message.data(), ':')
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
            return None
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), 'Client "')
            value = util.right_chop_and_strip(value, '" connected (')
            self._names.add(value)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), 'Dropped')
            value = util.right_chop_and_strip(value, 'from server (')
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
            return None
        return None
