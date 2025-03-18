# ALLOW core.* starbound.messaging
from core.msg import msgabc
from core.http import httprsc
from core.common import rconsvc, svrhelpers

_HELP_TEXT = '''STARBOUND CONSOLE HELP
help, ban, clearstagehand, disablespawning, enablespawning,
kick, list, placedungeon, resetuniverseflags, serverreload,
setspawnpoint, settileprotection, setuniverseflag, spawnitem,
spawnliquid, spawnmonster, spawnnpc, spawnstagehand, spawntreasure,
spawnvehicle, timewarp, unbanip, unbanuuiud, warp, whereis

Use help {command} to get detailed information.
Command output will be shown in the console log.
'''


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, '[rcon] '))


def resources(mailer: msgabc.MulticastMailer, resource: httprsc.WebResource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_rcon()
