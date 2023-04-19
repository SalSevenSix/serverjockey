from core.util import util, funcutil
from core.msg import msgabc, msgftr
from core.http import httpabc
from core.system import svrsvc


class ServerStatusHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return await svrsvc.ServerStatus.get_status(self._mailer, self)


class ServerCommandHandler(httpabc.PostHandler):
    COMMANDS = funcutil.callable_dict(
        svrsvc.ServerService,
        ('signal_start', 'signal_daemon', 'signal_restart', 'signal_stop', 'signal_delete'))

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def handle_post(self, resource, data):
        command = 'signal_' + str(util.get('command', data))
        if command not in ServerCommandHandler.COMMANDS:
            return httpabc.ResponseBody.BAD_REQUEST
        ServerCommandHandler.COMMANDS[command](self._mailer, self)
        return httpabc.ResponseBody.NO_CONTENT


class MaintenanceStateSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer, maintenance_filter: msgabc.Filter, ready_filter: msgabc.Filter):
        super().__init__(msgftr.Or(maintenance_filter, ready_filter))
        self._mailer = mailer
        self._maintenance_filter = maintenance_filter
        self._ready_filter = ready_filter

    def handle(self, message):
        if self._maintenance_filter.accepts(message):
            svrsvc.ServerStatus.notify_state(self._mailer, self, 'MAINTENANCE')
            return None
        if self._ready_filter.accepts(message):
            svrsvc.ServerStatus.notify_state(self._mailer, self, 'READY')
            return None
        return None
