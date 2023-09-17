# ALLOW core.* csgo.messaging
from core.util import util
from core.msg import msgabc
from core.http import httpabc, httprsc, httpext
from core.proc import proch
from core.common import interceptors, rconsvc


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
        self._mailer = mailer

    async def handle_post(self, resource, data):
        player, text = util.get('player', data), util.get('text', data)
        if not text or not player:
            return httpabc.ResponseBody.BAD_REQUEST
        lines = util.split_lines(text, lines_limit=5, total_char_limit=280)
        if not lines:
            return httpabc.ResponseBody.BAD_REQUEST
        for line in lines:
            if line:
                await proch.PipeInLineService.request(self._mailer, self, 'say ' + player + ': ' + line)
        return httpabc.ResponseBody.NO_CONTENT


HELP_TEXT = '''CSGO CONSOLE HELP
TODO
'''
