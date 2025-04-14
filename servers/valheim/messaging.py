# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import svrhelpers


DEFAULT_PORT = 2456
SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('Opened Steam server'))
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES, jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('Exception:'))


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    # context.register(_PlayerEventSubscriber(context))


# 04/13/2025 22:28:32: Valheim version: l-0.220.5 (network version 34)
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION = 'Valheim version:'
    VERSION_FILTER = msgftr.DataStrContains(VERSION)

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, _ServerDetailsSubscriber.VERSION_FILTER))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION)
        value = util.rchop(util.lchop(value, 'l-'), ' ')
        svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, version=value))
        return None
