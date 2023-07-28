# ALLOW util.* msg.* context.* http.* system.* EXCEPT system.bootstrap
from core.util import util, funcutil
from core.msg import msgabc, msgftr
from core.http import httpabc, httpsubs
from core.system import svrsvc


class ServerStatusHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return await svrsvc.ServerStatus.get_status(self._mailer, self)


class ServerCommandHandler(httpabc.PostHandler):
    COMMANDS = funcutil.callable_dict(
        svrsvc.ServerService, ('signal_start', 'signal_restart', 'signal_stop', 'signal_delete'))

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        command = 'signal_' + str(util.get('command', data))
        if command not in ServerCommandHandler.COMMANDS:
            return httpabc.ResponseBody.BAD_REQUEST
        respond, response = util.get('respond', data, False), {}
        if respond:
            subscription_path = await httpsubs.HttpSubscriptionService.subscribe(
                self._mailer, self, httpsubs.Selector(svrsvc.ServerStatus.UPDATED_FILTER))
            response['url'] = util.get('baseurl', data, '') + subscription_path
            response['current'] = await svrsvc.ServerStatus.get_status(self._mailer, self)
        ServerCommandHandler.COMMANDS[command](self._mailer, self)
        return response if respond else httpabc.ResponseBody.NO_CONTENT


class CheckServerStateInterceptor(httpabc.InterceptorHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, delegate: httpabc.ABC_HANDLER,
                 running: bool = None, states: tuple = None):
        self._mailer = mailer
        self._delegate = delegate
        self._running = running
        self._states = states if states else ()

    def allows(self, method: httpabc.Method) -> bool:
        return httpabc.AllowMethod.call(method, self._delegate)

    async def handle_get(self, resource, data):
        return await httpabc.GetHandler.call(self._delegate, resource, data)

    async def handle_post(self, resource, data):
        status = await svrsvc.ServerStatus.get_status(self._mailer, self)
        if self._running is not None and self._running == status['running']:
            return httpabc.ResponseBody.CONFLICT
        for state in self._states:
            if state == status['state']:
                return httpabc.ResponseBody.CONFLICT
        return await httpabc.PostHandler.call(self._delegate, resource, data)


class MaintenanceStateSubscriber(msgabc.AbcSubscriber):
    READY, MAINTENANCE = 'READY', 'MAINTENANCE'

    def __init__(self, mailer: msgabc.Mailer, maintenance_filter: msgabc.Filter, ready_filter: msgabc.Filter):
        super().__init__(msgftr.Or(maintenance_filter, ready_filter))
        self._mailer = mailer
        self._maintenance_filter = maintenance_filter
        self._ready_filter = ready_filter

    def handle(self, message):
        if self._maintenance_filter.accepts(message):
            svrsvc.ServerStatus.notify_state(self._mailer, self, MaintenanceStateSubscriber.MAINTENANCE)
            return None
        if self._ready_filter.accepts(message):
            svrsvc.ServerStatus.notify_state(self._mailer, self, MaintenanceStateSubscriber.READY)
            return None
        return None
