# ALLOW core.* palworld.messaging
from core.msg import msgabc
from core.http import httpabc
from core.common import rconsvc, svrhelpers

# https://tech.palworldgame.com/settings-and-operation/commands/
_HELP_TEXT = '''PALWORLD CONSOLE COMMANDS
Info          Show server information
ShowPlayers   Show information on all connected players
Save          Save the world data
Broadcast {Message}   Send message to all player on the server
KickPlayer {SteamID}  Kick player by SteamID from the server
BanPlayer {SteamID}   Ban player by SteamID from the server
'''


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, enforce_id=False))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_rcon()
