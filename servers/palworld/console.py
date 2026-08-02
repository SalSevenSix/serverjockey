# ALLOW core.* palworld.messaging
from core.util import util
from core.msg import msgabc
from core.http import httpabc, httprsc
from core.common import rconsvc, svrhelpers
from core.proc import prcext

# https://tech.palworldgame.com/settings-and-operation/commands/
_HELP_TEXT = '''PALWORLD CONSOLE COMMANDS
Info          Show server information
ShowPlayers   Show information on all connected players
Save          Save the world data
Broadcast {Message}  Send message to all player on the server
KickPlayer {UserId}  Kick player by SteamID from the server
BanPlayer {UserId}   Ban player by SteamID from the server
'''


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, enforce_id=False))


def resources(mailer: msgabc.MulticastMailer, resource: httprsc.WebResource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_rcon()
    builder.put('say', _SayHandler(mailer, 'Broadcast {player}: {line}'), 's')


# This is a copy of prcext.SayHandler
class _SayHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, template: str):
        self._mailer = mailer
        self._formatter = prcext.TemplateSayFormatter(template)

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
            await rconsvc.RconService.request(self._mailer, self, self._formatter.cmdline(player, line))
        return httpabc.ResponseBody.NO_CONTENT
