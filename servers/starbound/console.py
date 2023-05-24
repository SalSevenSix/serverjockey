# ALLOW core.* starbound.messaging
from core.msg import msgabc
from core.http import httpabc, httprsc, httpext
from core.common import rconsvc, interceptors


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, '[rcon] '))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', httpext.StaticHandler(HELP_TEXT))
    r.put('send', rconsvc.RconHandler(mailer), 's')


HELP_TEXT = '''STARBOUND CONSOLE COMMANDS
help, ban, clearstagehand, disablespawning, enablespawning,
kick, listplacedungeon, resetuniverseflags, serverreload,
setspawnpoint, settileprotection, setuniverseflag, spawnitem,
spawnliquid, spawnmonster, spawnnpc, spawnstagehand, spawntreasure,
spawnvehicle, timewarp, unbanip, unbanuuiud, warp, whereis

Use help {command} to get detailed documentation.
Command output will be shown in the console log.
'''
