# ALLOW core.* factorio.messaging
from core.util import util
from core.msg import msgabc
from core.http import httpabc, httprsc, httpext
from core.common import rconsvc, interceptors


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, 'RCON> '))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', httpext.StaticHandler(HELP_TEXT))
    r.put('send', rconsvc.RconHandler(mailer), 's')
    r.put('say', _SayHandler(mailer), 's')


class _SayHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._delegate = rconsvc.RconHandler(mailer)

    async def handle_post(self, resource, data):
        player, text = util.get('player', data), util.get('text', data)
        if not text or not player:
            return httpabc.ResponseBody.BAD_REQUEST
        lines = util.split_lines(text, lines_limit=5, total_char_limit=280)
        if not lines:
            return httpabc.ResponseBody.BAD_REQUEST
        for line in lines:
            if line:
                data['line'] = player + ': ' + line
                response = await httpabc.PostHandler.call(self._delegate, resource, data)
                if response is not httpabc.ResponseBody.NO_CONTENT:
                    return response
        return httpabc.ResponseBody.NO_CONTENT


HELP_TEXT = '''FACTORIO CONSOLE HELP
Console input that does not start with / is shown as a chat message.
Command output will be shown in the console log.
Note that some commands only work on the in-game console.
Help on commands can be found on the Factorio wiki.
  https://wiki.factorio.com/Console
'''
