# ALLOW core.* palworld.messaging
from core.msg import msgabc
from core.http import httpabc, httprsc, httpext
from core.common import interceptors, rconsvc

# https://tech.palworldgame.com/settings-and-operation/commands/


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, enforce_id=False))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', httpext.StaticHandler(HELP_TEXT))
    r.put('send', rconsvc.RconHandler(mailer), 's')


HELP_TEXT = '''PALWORLD CONSOLE COMMANDS
Info          Show server information
ShowPlayers   Show information on all connected players
Save          Save the world data
Broadcast {Message}   Send message to all player on the server
KickPlayer {SteamID}  Kick player by SteamID from the server
BanPlayer {SteamID}   Ban player by SteamID from the server
'''
