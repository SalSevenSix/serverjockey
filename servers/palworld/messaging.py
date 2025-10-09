# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import rconsvc, svrhelpers


_SERVER_VERSION_KEY = 'Game version is'
_SERVER_VERSION_FILTER = msgftr.DataStrStartsWith(_SERVER_VERSION_KEY)
SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, _SERVER_VERSION_FILTER)
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES, rconsvc.RconService.FILTER_OUTPUT,
    jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))


# Game version is v0.3.10.61027
# Running Palworld dedicated server on :8211
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    PORT_FILTER = msgftr.DataStrStartsWith('Running Palworld dedicated server on')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_ALL_LINES,
            msgftr.Or(_SERVER_VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        if _SERVER_VERSION_FILTER.accepts(message):
            version = util.lchop(message.data(), _SERVER_VERSION_KEY)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            port = util.lchop(message.data(), ':')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=port))
        return None
