from core import msgabc, proch, svrsvc, util


class ServerStateSubscriber(msgabc.Subscriber):
    STATE_MAP = {
        proch.ProcessHandler.STATE_START: 'START',
        proch.ProcessHandler.STATE_STARTING: 'STARTING',
        proch.ProcessHandler.STATE_STARTED: 'STARTED',
        proch.ProcessHandler.STATE_TIMEOUT: 'TIMEOUT',
        proch.ProcessHandler.STATE_TERMINATED: 'TERMINATED',
        proch.ProcessHandler.STATE_EXCEPTION: 'EXCEPTION',
        proch.ProcessHandler.STATE_COMPLETE: 'COMPLETE',
    }

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def accepts(self, message):
        return proch.Filter.PROCESS_STATE_ALL.accepts(message)

    def handle(self, message):
        state = util.get(message.name(), ServerStateSubscriber.STATE_MAP)
        svrsvc.ServerStatus.notify_state(self._mailer, self, state if state else 'UNKNOWN')
        if message.name() is proch.ProcessHandler.STATE_EXCEPTION:
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'exception': repr(message.data())})
        return None
