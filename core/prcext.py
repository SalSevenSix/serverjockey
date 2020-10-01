from core import msgabc, proch, svrsvc, util


class ServerStateSubscriber(msgabc.Subscriber):
    STATE_MAP = {
        proch.ServerProcess.STATE_START: 'START',
        proch.ServerProcess.STATE_STARTING: 'STARTING',
        proch.ServerProcess.STATE_STARTED: 'STARTED',
        proch.ServerProcess.STATE_TIMEOUT: 'TIMEOUT',
        proch.ServerProcess.STATE_TERMINATED: 'TERMINATED',
        proch.ServerProcess.STATE_EXCEPTION: 'EXCEPTION',
        proch.ServerProcess.STATE_COMPLETE: 'COMPLETE',
    }

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def accepts(self, message):
        return proch.ServerProcess.FILTER_STATE_ALL.accepts(message)

    def handle(self, message):
        state = util.get(message.name(), ServerStateSubscriber.STATE_MAP)
        svrsvc.ServerStatus.notify_state(self._mailer, self, state if state else 'UNKNOWN')
        if message.name() is proch.ServerProcess.STATE_EXCEPTION:
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'exception': repr(message.data())})
        return None
