# ALLOW const.* util.* msg*.* context.* http.* system.* proc.*
from core.util import cmdutil, util
from core.msg import msgabc
from core.http import httpabc
from core.system import svrsvc
from core.proc import proch


class ServerStateSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(proch.ServerProcess.FILTER_STATE_ALL)
        self._mailer = mailer

    def handle(self, message):
        name, data = message.name(), message.data()
        state = util.left_chop_and_strip(name, '.').upper()
        details = {'error': str(data)} if name is proch.ServerProcess.STATE_EXCEPTION else None
        svrsvc.ServerStatus.notify_status(self._mailer, self, state, details)
        return None


class ConsoleCommandHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, commands: cmdutil.CommandLines):
        self._mailer, self._commands = mailer, commands

    async def handle_post(self, resource, data):
        cmdline = self._commands.get(data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT
