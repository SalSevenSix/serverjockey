# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.common import svrhelpers

SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('|INFO    |VirtualServerBase|1  |listening on'))
DEPLOYMENT_START, DEPLOYMENT_DONE = 'Deployment.Start', 'Deployment.Done'
FILTER_DEPLOYMENT_START, FILTER_DEPLOYMENT_DONE = msgftr.NameIs(DEPLOYMENT_START), msgftr.NameIs(DEPLOYMENT_DONE)
CONSOLE_LOG_FILTER = msgftr.Or(mc.ServerProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, msgftr.DataStrContains('|ERROR   |'))


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state(FILTER_DEPLOYMENT_START, FILTER_DEPLOYMENT_DONE).init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.local_ip()))


# 2025-11-07 13:55:07.560454|INFO    |ServerLibPriv |   |TeamSpeak 3 Server 3.13.7 (2022-06-20 12:21:53)
# 2025-11-07 13:55:08.409180|INFO    |VirtualServerBase|1  |listening on 0.0.0.0:9987, [::]:9987
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*\|INFO    \|ServerLibPriv \|   \|TeamSpeak 3 Server (.*?) \(.*')

    def __init__(self, mailer: msgabc.Mailer, local_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerDetailsSubscriber.VERSION_FILTER, SERVER_STARTED_FILTER)))
        self._mailer, self._local_ip = mailer, local_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif SERVER_STARTED_FILTER.accepts(message):
            port = util.rchop(util.lchop(util.lchop(message.data(), 'listening on'), ':'), ',')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._local_ip, port=port))
        return None
