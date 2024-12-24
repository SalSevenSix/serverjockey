# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.msgc import mc
from core.system import svrsvc, svrext
from core.proc import jobh, prcext
from core.common import rconsvc, playerstore

_SPAM = r'^src/steamnetworkingsockets/clientlib/steamnetworkingsockets_lowlevel.cpp(.*):' \
        r' Assertion Failed: usecElapsed >= 0$'

SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataMatches(r'^SV: .* player server started$'))
CONSOLE_LOG_FILTER = msgftr.Or(
    msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, msgftr.HasData(), msgftr.Not(msgftr.Or(
        msgftr.DataStrContains('UNEXPECTED LONG FRAME DETECTED'), msgftr.DataMatches(_SPAM)))),
    rconsvc.RconService.FILTER_OUTPUT,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS)
MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(_ServerDetailsSubscriber(mailer, await sysutil.public_ip()))
    mailer.register(_PlayerEventSubscriber(mailer))


# GC Connection established for server version 2000166, instance idx 1
# Network socket 'server' opened on port 27015
# Host activate: Loading (de_dust2)
# Host activate: Changelevel (de_inferno)

class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    MAP_FILTER = msgftr.DataMatches(r'^Host activate: (Loading|Changelevel) \(.*\)$')
    VERSION_FILTER = msgftr.DataMatches(r'^GC Connection established for server version .*, instance idx.*')
    PORT_FILTER = msgftr.DataMatches(r'^Network socket \'server\' opened on port.*')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.MAP_FILTER,
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.MAP_FILTER.accepts(message):
            value = util.lchop(message.data(), '(')[:-1]
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'map': value})
            return None
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), 'server version')
            value = util.rchop(value, ',')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=value))
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), 'port')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=value))
            return None
        return None


# [All Chat][Apollo (8723357)]: Hello from Game
# say Hello from console
# [All Chat][Console (0)]: @sjgms: Hello from Discord

# Client #2 "Apollo" connected @ 192.168.0.104:63939
# SV:  Dropped client 'Apollo' from server(2): NETWORK_DISCONNECT_DISCONNECT_BY_USER

class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT_FILTER = msgftr.DataMatches(r'^\[All Chat\]\[.* \(.*\)\]: .*')
    JOIN_FILTER = msgftr.DataMatches(r'^Client .* ".*" connected @ .*')
    LEAVE_FILTER = msgftr.DataMatches(r'^SV:  Dropped client \'.*\' from server.*')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            msgftr.Or(mc.ServerProcess.FILTER_STDOUT_LINE,
                      rconsvc.RconService.FILTER_OUTPUT),
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            if message.data().startswith('[All Chat][Console (0)]: @'):
                return None
            name = util.lchop(message.data(), '[All Chat][')
            name = util.rchop(name, '(')
            text = util.lchop(message.data(), ')]:')
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
            return None
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.lchop(message.data(), ' "')
            value = util.rchop(value, '" connected')
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.lchop(message.data(), 'Dropped client \'')
            value = util.rchop(value, '\' from server')
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
            return None
        return None
