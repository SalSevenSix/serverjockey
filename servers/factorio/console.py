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


HELP_TEXT = '''FACTORIO CONSOLE HELP
Console input that does not start with / is shown as a chat message.
Command output will be shown in the console log.
Note that some commands only work on the in-game console.
Help on commands can be found on the Factorio wiki.
  https://wiki.factorio.com/Console
'''
