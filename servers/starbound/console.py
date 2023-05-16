# ALLOW core.* starbound.messaging
from core.msg import msgabc
from core.http import httpabc, httprsc
from core.common import rconsvc, interceptors


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, '[rcon] '))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', _ConsoleHelpHandler())
    r.put('send', rconsvc.RconHandler(mailer), 's')


class _ConsoleHelpHandler(httpabc.GetHandler):

    def handle_get(self, resource, data):
        return '''STARBOUND CONSOLE COMMANDS
help, ban, clearstagehand, disablespawning, enablespawning,
kick, listplacedungeon, resetuniverseflags, serverreload,
setspawnpoint, settileprotection, setuniverseflag, spawnitem,
spawnliquid, spawnmonster, spawnnpc, spawnstagehand, spawntreasure,
spawnvehicle, timewarp, unbanip, unbanuuiud, warp, whereis

Use help {command} to get detailed documentation.
Command output will be shown in the console log.
'''
