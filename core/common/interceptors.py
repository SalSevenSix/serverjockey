# ALLOW const.* util.* msg.* context.* http.* system.* proc.*
from core.msg import msgabc
from core.http import httpabc
from core.system import svrext

_STATES_NOT_STARTED = ('START', 'STARTING', 'STOPPING')
_STATES_MAINTENANCE = (svrext.MaintenanceStateSubscriber.MAINTENANCE,)


def block_not_started(mailer: msgabc.MulticastMailer) -> httpabc.InterceptorBuilder:
    return _CheckServerStateInterceptorBuilder(mailer, running=False, states=_STATES_NOT_STARTED)


def block_running_or_maintenance(mailer: msgabc.MulticastMailer) -> httpabc.InterceptorBuilder:
    return _CheckServerStateInterceptorBuilder(mailer, running=True, states=_STATES_MAINTENANCE)


def block_maintenance_only(mailer: msgabc.MulticastMailer) -> httpabc.InterceptorBuilder:
    return _CheckServerStateInterceptorBuilder(mailer, states=_STATES_MAINTENANCE)


class _CheckServerStateInterceptorBuilder(httpabc.InterceptorBuilder):

    def __init__(self, mailer: msgabc.MulticastMailer, running: bool = None, states: tuple = None):
        self._mailer, self._running, self._states = mailer, running, states

    def wrap(self, handler):
        return svrext.CheckServerStateInterceptor(self._mailer, handler, self._running, self._states)
