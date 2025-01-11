# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.msgc import mc
from core.system import svrsvc, svrext
from core.proc import jobh, prcext
from core.common import playerstore, rconsvc

SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataMatches(
        '.*Info CommandLineMultiplayer.*Maximum segment size.*maximum-segment-size.*minimum-segment-size.*'))
DEPLOYMENT_MSG, DEPLOYMENT_START, DEPLOYMENT_DONE = 'Deployment.Message', 'Deployment.Start', 'Deployment.Done'
FILTER_DEPLOYMENT_MSG = msgftr.NameIs(DEPLOYMENT_MSG)
FILTER_DEPLOYMENT_START = msgftr.NameIs(DEPLOYMENT_START)
FILTER_DEPLOYMENT_DONE = msgftr.NameIs(DEPLOYMENT_DONE)
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES,
    jobh.JobProcess.FILTER_ALL_LINES,
    rconsvc.RconService.FILTER_OUTPUT,
    msglog.FILTER_ALL_LEVELS,
    FILTER_DEPLOYMENT_MSG)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.DataMatches(r'^\d*\.\d* Error .*'))
MAINTENANCE_STATE_FILTER = msgftr.Or(
    FILTER_DEPLOYMENT_START, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(
    FILTER_DEPLOYMENT_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(_ServerDetailsSubscriber(mailer, await sysutil.local_ip()))
    mailer.register(_PlayerEventSubscriber(mailer))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches('.*; Factorio .*build .* headless.*')
    PORT_FILTER = msgftr.DataStrContains('Hosting game at IP ADDR:')
    IP_FILTER = msgftr.Or(
        msgftr.DataMatches('.*Info.*Own address is IP ADDR.*confirmed by pingpong.*'),
        msgftr.DataMatches('.*Warning.*Determining own address has failed. Best guess: IP ADDR.*'))

    def __init__(self, mailer: msgabc.Mailer, local_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _ServerDetailsSubscriber.IP_FILTER)))
        self._mailer, self._local_ip = mailer, local_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), 'Factorio')
            value = util.rchop(value, '(build')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=value))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), '({')
            value = util.rchop(value, '})')
            value = value.split(':')
            if value[0] == '0.0.0.0':
                value[0] = self._local_ip
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=value[0], port=value[1]))
        elif _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.lchop(message.data(), '({')
            value = util.rchop(value, '})')
            value = value.split(':')
            if value[0] == '0.0.0.0':
                value[0] = self._local_ip
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=value[0]))
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT, JOIN, LEAVE, KICK = '[CHAT]', '[JOIN]', '[LEAVE]', '[KICK]'
    CHAT_FILTER = msgftr.DataStrContains(CHAT)
    JOIN_FILTER = msgftr.DataStrContains(JOIN)
    LEAVE_FILTER = msgftr.DataStrContains(LEAVE)
    KICK_FILTER = msgftr.DataStrContains(KICK)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.LEAVE_FILTER,
                      _PlayerEventSubscriber.KICK_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.CHAT)
            name, text = util.rchop(value, ':'), util.lchop(value, ':')
            if name == '<server>' and text.startswith('@'):
                return None  # Ignore chat messages from /console/say command
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
            return None
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.JOIN)
            value = util.rchop(value, 'joined the game')
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
        elif _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.LEAVE)
            value = util.rchop(value, 'left the game')
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
        elif _PlayerEventSubscriber.KICK_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.KICK)
            value = util.rchop(value, 'was kicked by')
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
        return None
