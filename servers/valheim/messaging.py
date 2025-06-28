# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import svrhelpers, playerstore


DEFAULT_PORT, NAME_PORT = 2456, 'messaging.Port'
SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('Opened Steam server'))
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES, jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('Exception:'))


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))


# 04/13/2025 22:28:32: Valheim version: l-0.220.5 (network version 34)
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION = 'Valheim version:'

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.Or(
            msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains(_ServerDetailsSubscriber.VERSION)),
            msgftr.NameIs(NAME_PORT)))
        self._mailer, self._public_ip, self._port = mailer, public_ip, str(DEFAULT_PORT)

    def handle(self, message):
        if message.name() is NAME_PORT:
            self._port = str(message.data())
            return None
        value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION)
        value = util.rchop(util.lchop(value, 'l-'), ' ')
        svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=self._port, version=value))
        return None


# 06/28/2025 14:37:28: Got handshake from client 123456789
# 06/28/2025 14:37:46: Got character ZDOID from Jojo : -192694289:3
# 06/28/2025 14:38:49: Closing socket 123456789
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    LOGIN, LOGOUT = ': Got handshake from client', ': Closing socket'
    LOGIN_FILTER = msgftr.DataStrContains(LOGIN)
    LOGOUT_FILTER = msgftr.DataStrContains(LOGOUT)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.LOGIN_FILTER, _PlayerEventSubscriber.LOGOUT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.LOGIN)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
        elif _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.LOGOUT)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
        return None
