# ALLOW core.*
from core.util import util
from core.msg import msgabc, msgftr, msglog, msgext
from core.msgc import mc
from core.system import svrext, svrsvc
from core.proc import jobh, prcext
from core.common import rconsvc


SERVER_VERSION_KEY = 'Game version is'
SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.DataStrStartsWith(SERVER_VERSION_KEY))
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES,
    rconsvc.RconService.FILTER_OUTPUT,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS)
_MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
_READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, _MAINTENANCE_STATE_FILTER, _READY_STATE_FILTER))
    mailer.register(_ServerDetailsSubscriber(mailer))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(SERVER_STARTED_FILTER)
        self._mailer = mailer

    def handle(self, message):
        value = util.lchop(message.data(), SERVER_VERSION_KEY)
        svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
        return None
