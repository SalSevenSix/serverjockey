import typing
from core.util import cmdutil, util
from core.msg import msgabc
from core.http import httpabc
from core.proc import proch
from core.system import svrsvc


class ServerStateSubscriber(msgabc.AbcSubscriber):
    STATE_MAP = {
        proch.ServerProcess.STATE_START: 'START',
        proch.ServerProcess.STATE_STARTING: 'STARTING',
        proch.ServerProcess.STATE_STARTED: 'STARTED',
        proch.ServerProcess.STATE_TIMEOUT: 'TIMEOUT',
        proch.ServerProcess.STATE_TERMINATED: 'TERMINATED',
        proch.ServerProcess.STATE_EXCEPTION: 'EXCEPTION',
        proch.ServerProcess.STATE_COMPLETE: 'COMPLETE'
    }

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(proch.ServerProcess.FILTER_STATE_ALL)
        self._mailer = mailer

    def handle(self, message):
        name = message.name()
        state = util.get(name, ServerStateSubscriber.STATE_MAP)
        svrsvc.ServerStatus.notify_state(self._mailer, self, state if state else 'UNKNOWN')
        if name is proch.ServerProcess.STATE_EXCEPTION:
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'error': repr(message.data())})
        return None


class PipeInLineNoContentPostHandler(httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, source: typing.Any, commands: cmdutil.CommandLines):
        self._mailer = mailer
        self._source = source
        self._commands = commands

    async def handle_post(self, resource, data):
        cmdline = self._commands.get(data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self._source, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT
