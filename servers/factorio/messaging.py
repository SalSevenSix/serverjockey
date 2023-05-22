# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.system import svrsvc, svrext
from core.proc import proch, jobh, prcext
from core.common import playerstore

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataMatches(
        '.*Info CommandLineMultiplayer.*Maximum segment size.*maximum-segment-size.*minimum-segment-size.*'))
DEPLOYMENT_MSG, INSTALL_START, INSTALL_DONE = 'Deployment.Message', 'Install.Start', 'Install.Done'
FILTER_DEPLOYMENT_MSG = msgftr.NameIs(DEPLOYMENT_MSG)
FILTER_INSTALL_START = msgftr.NameIs(INSTALL_START)
FILTER_INSTALL_DONE = msgftr.NameIs(INSTALL_DONE)
CONSOLE_LOG_FILTER = msgftr.Or(
    proch.ServerProcess.FILTER_ALL_LINES,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.LoggingPublisher.FILTER_ALL_LEVELS,
    FILTER_DEPLOYMENT_MSG)
MAINTENANCE_STATE_FILTER = msgftr.Or(FILTER_INSTALL_START, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(FILTER_INSTALL_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(_ServerDetailsSubscriber(mailer, await sysutil.get_local_ip()))
    mailer.register(_PlayerEventSubscriber(mailer))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches('.*; Factorio .*build .* headless.*')
    PORT_FILTER = msgftr.DataStrContains('Hosting game at IP ADDR:')
    IP_FILTER = msgftr.Or(
        msgftr.DataMatches('.*Info.*Own address is IP ADDR.*confirmed by pingpong.*'),
        msgftr.DataMatches('.*Warning.*Determining own address has failed. Best guess: IP ADDR.*'))

    def __init__(self, mailer: msgabc.MulticastMailer, local_ip: str):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _ServerDetailsSubscriber.IP_FILTER)))
        self._mailer = mailer
        self._local_ip = local_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), 'Factorio')
            value = util.right_chop_and_strip(value, '(build')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), '({')
            value = util.right_chop_and_strip(value, '})')
            value = value.split(':')
            if value[0] == '0.0.0.0':
                value[0] = self._local_ip
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': value[0], 'port': value[1]})
            return None
        if _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), '({')
            value = util.right_chop_and_strip(value, '})')
            value = value.split(':')
            if value[0] == '0.0.0.0':
                value[0] = self._local_ip
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': value[0]})
            return None
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    JOIN, LEAVE = '[JOIN]', '[LEAVE]'
    JOIN_FILTER = msgftr.DataStrContains(JOIN)
    LEAVE_FILTER = msgftr.DataStrContains(LEAVE)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.JOIN_FILTER, _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.JOIN)
            value = util.right_chop_and_strip(value, 'joined the game')
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.LEAVE)
            value = util.right_chop_and_strip(value, 'left the game')
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
            return None
        return None
