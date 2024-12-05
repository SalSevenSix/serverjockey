# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.msgc import mc
from core.system import svrext, svrsvc
from core.proc import jobh, prcext
from core.common import rconsvc


_SERVER_VERSION_KEY = 'Game version is'
_SERVER_VERSION_FILTER = msgftr.DataStrStartsWith(_SERVER_VERSION_KEY)
SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, _SERVER_VERSION_FILTER)
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES,
    rconsvc.RconService.FILTER_OUTPUT,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS)
_MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
_READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, _MAINTENANCE_STATE_FILTER, _READY_STATE_FILTER))
    mailer.register(await _ServerDetailsSubscriber(mailer).initialise())


# Game version is v0.3.10.61027
# Running Palworld dedicated server on :8211
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    PORT_FILTER = msgftr.DataStrStartsWith('Running Palworld dedicated server on')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_ALL_LINES,
            msgftr.Or(_SERVER_VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer, self._ip = mailer, None

    async def initialise(self) -> msgabc.Subscriber:
        self._ip = await sysutil.public_ip()
        return self

    def handle(self, message):
        if _SERVER_VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _SERVER_VERSION_KEY)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), ':')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': self._ip, 'port': value})
            return None
        return None
