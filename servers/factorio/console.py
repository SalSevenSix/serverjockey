# ALLOW core.* factorio.messaging
from core.msg import msgabc
from core.http import httpabc, httprsc, httpext
from core.common import rconsvc, interceptors


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, 'RCON> '))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', httpext.StaticHandler(HELP_TEXT))
    r.put('send', rconsvc.RconHandler(mailer), 's')


HELP_TEXT = '''FACTORIO CONSOLE
Console input that does not start with / is shown as a chat message to your team. 
Help on commands can be found on the Factorio wiki. Note that some commands
only work on the in-game console.
  https://wiki.factorio.com/Console
'''