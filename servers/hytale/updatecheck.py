import asyncio
# ALLOW core.* hytale.messaging
from core.msg import msgabc, msgftr, msgext
from core.msgc import mc
from core.http import httpabc, httprsc, httpsec
from core.proc import proch, prcext
from core.common import interceptors
from servers.hytale import messaging as msg

_CHECK_COMMAND = 'update check'
_SET_MINUTES = 'updatecheck.SET_MINUTES'
_LATEST_FILTER = msgftr.DataStrStartsWith('Already running the latest version:')
_STALE_FILTER = msgftr.DataStrStartsWith('Update available:')


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(_UpdateCheckSubscriber(mailer))
    mailer.register(_UpdateRequiredSubscriber(mailer))


def resources(mailer: msgabc.MulticastMailer, resource: httprsc.WebResource):
    builder = httprsc.ResourceBuilder(resource)
    builder.reg('s', interceptors.block_not_started(mailer))
    builder.put('updatecheck', _UpdateCheckHandler(mailer), 's')


def set_check_update_minutes(mailer: msgabc.Mailer, source: any, value: int | None):
    mailer.post(source, _SET_MINUTES, value if value else 0)


class _UpdateCheckSubscriber(msgabc.AbcSubscriber):
    SET_MINUTES_FILTER = msgftr.NameIs(_SET_MINUTES)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            _UpdateCheckSubscriber.SET_MINUTES_FILTER, mc.ServerProcess.FILTER_STATE_STARTED,
            mc.ServerProcess.FILTER_STATE_STOPPING, mc.ServerProcess.FILTER_STATES_DOWN,
            msg.UPDATE_REQUIRED_FILTER))
        self._mailer, self._seconds = mailer, 0.0
        self._checker = prcext.TimedConsoleCommand(mailer, _CHECK_COMMAND, self._seconds)

    async def handle(self, message):
        if _UpdateCheckSubscriber.SET_MINUTES_FILTER.accepts(message):
            self._seconds = float(message.data() * 60.0) if message.data() else 0.0
        elif mc.ServerProcess.FILTER_STATE_STARTED.accepts(message):
            self._checker.stop()
            if self._seconds > 0.0:
                await asyncio.sleep(2.0)
                await proch.PipeInLineService.request(self._mailer, self, _CHECK_COMMAND)
            self._checker = prcext.TimedConsoleCommand(self._mailer, _CHECK_COMMAND, self._seconds)
            self._checker.start()
        elif (mc.ServerProcess.FILTER_STATE_STOPPING.accepts(message)
                or mc.ServerProcess.FILTER_STATES_DOWN.accepts(message)
                or msg.UPDATE_REQUIRED_FILTER.accepts(message)):
            self._checker.stop()
        return None


class _UpdateRequiredSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, _STALE_FILTER))
        self._mailer = mailer

    async def handle(self, message):
        self._mailer.post(self, msg.UPDATE_REQUIRED)
        await asyncio.sleep(1.0)
        await proch.PipeInLineService.request(self._mailer, self, 'say SERVER UPDATE REQUIRED')
        return None


class _UpdateCheckHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        response = await proch.PipeInLineService.request(
            self._mailer, self, _CHECK_COMMAND, msgext.SingleCatcher(
                msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.Or(_LATEST_FILTER, _STALE_FILTER)),
                timeout=10.0))
        result = _STALE_FILTER.accepts(response) if response else None
        return dict(result=result)
