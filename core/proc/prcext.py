# ALLOW util.* msg*.* context.* http.* system.* proc.*
from core.util import cmdutil, util
from core.msg import msgabc
from core.msgc import mc
from core.http import httpabc
from core.system import svrsvc
from core.proc import proch


class ServerStateSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(mc.ServerProcess.FILTER_STATE_ALL)
        self._mailer = mailer

    def handle(self, message):
        name, data = message.name(), message.data()
        state = util.lchop(name, '.').upper()
        details = dict(error=str(data)) if name is mc.ServerProcess.STATE_EXCEPTION else None
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


class SayHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, template: str):
        self._mailer, self._template = mailer, template

    async def handle_post(self, resource, data):
        player, text = util.get('player', data), util.get('text', data)
        player, text = player.strip() if player else player, text.strip() if text else text
        if not text:
            return httpabc.ResponseBody.NO_CONTENT
        if not player:
            return httpabc.ResponseBody.BAD_REQUEST
        if player == '@':  # This is the Chatbot
            lines = text.split('\n')
        else:
            lines = util.split_lines(text, lines_limit=5, total_char_limit=280)
        if not lines:
            return httpabc.ResponseBody.BAD_REQUEST
        for line in [o.strip() for o in lines if o]:
            await proch.PipeInLineService.request(self._mailer, self, self._template.format(player=player, line=line))
        return httpabc.ResponseBody.NO_CONTENT
