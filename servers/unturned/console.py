# ALLOW core.* unturned.messaging
from core.util import cmdutil
from core.msg import msgabc
from core.http import httpabc, httprsc, httpext
from core.proc import prcext
from core.common import interceptors

_COMMANDS = cmdutil.CommandLines({'send': '{line}'})


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', httpext.StaticHandler(HELP_TEXT))
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _COMMANDS), 's')


HELP_TEXT = '''UNTURNED CONSOLE HELP
Use Help to see list of commands. 
Use Help {command} to get detailed information.
Command output will be shown in the console log.
More help on commands can be found on the wiki.
  https://unturned.fandom.com/wiki/Server_Commands
'''
