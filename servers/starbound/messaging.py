# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.system import svrsvc, svrext
from core.proc import proch, jobh, prcext
from core.common import playerstore

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('[Info] Root: Writing runtime configuration to'))
CONSOLE_LOG_FILTER = msgftr.Or(
    proch.ServerProcess.FILTER_ALL_LINES,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.LoggingPublisher.FILTER_ALL_LEVELS)
MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(_ServerDetailsSubscriber(mailer, await sysutil.get_public_ip()))
    mailer.register(_PlayerEventSubscriber(mailer))


# [Info] Server Version 1.4.4 (linux x86_64) Source ID: 8cbe6faf22282659828a194e06a08999f213769e Protocol: 747
# [Info] UniverseServer: listening for incoming TCP connections on 0000:0000:0000:0000:0000:0000:0000:0000:21025

class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_PREFIX, VERSION_SUFFIX = '[Info] Server Version', 'Source ID:'
    VERSION_FILTER = msgftr.DataMatches(
        '.*' + VERSION_PREFIX.replace('[', '\[').replace(']', '\]') + '.*' + VERSION_SUFFIX + '.*')
    PORT_FILTER = msgftr.DataStrContains('[Info] UniverseServer: listening for incoming TCP connections on')

    def __init__(self, mailer: msgabc.MulticastMailer, public_ip: str):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerDetailsSubscriber.VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer = mailer
        self._public_ip = public_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.right_chop_and_strip(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            value = util.right_chop_and_strip(value, '(')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = message.data()
            value = value[value.rfind(':') + 1:]
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': self._public_ip, 'port': value})
            return None
        return None


# [Info] UniverseServer: Logged in account '<anonymous>' as player 'Jazmin' from address 00:0000:ffff:c0a8:0065
# [Info] UniverseServer: Client 'Jazmin' <1> (0000:0000:0000:0000:0000:ffff:c0a8:0065) connected
# [Info] UniverseServer: Client 'Jazmin' <1> (0000:0000:0000:0000:0000:ffff:c0a8:0065) disconnected for reason:

class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    PREFIX = '[Info] UniverseServer: Client'
    REG_PREFIX = '.*' + PREFIX.replace('[', '\[').replace(']', '\]')
    CONNECT_FILTER = msgftr.DataMatches(REG_PREFIX + '.*\) connected.*')
    DISCONNECT_FILTER = msgftr.DataMatches(REG_PREFIX + '.*\) disconnected for reason.*')

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CONNECT_FILTER, _PlayerEventSubscriber.DISCONNECT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.PREFIX)[1:]
        value = util.right_chop_and_strip(value, "' ")
        if _PlayerEventSubscriber.CONNECT_FILTER.accepts(message):
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.DISCONNECT_FILTER.accepts(message):
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
            return None
        return None
