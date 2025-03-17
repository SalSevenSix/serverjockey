# ALLOW core.* factorio.messaging
from core.msg import msgabc
from core.http import httpabc
from core.common import rconsvc, svrhelpers

_HELP_TEXT = '''FACTORIO CONSOLE HELP
Console input that does not start with / is shown as a chat message.
Command output will be shown in the console log.
Note that some commands only work on the in-game console.
Help on commands can be found on the Factorio wiki.
  https://wiki.factorio.com/Console
'''


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, 'RCON> '))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_rcon().put_say_pipein('{player}: {line}')
