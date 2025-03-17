# ALLOW core.* csii.messaging
from core.msg import msgabc
from core.http import httpabc
from core.common import rconsvc, svrhelpers

_HELP_TEXT = '''CS2 CONSOLE HELP
Help on commands can be found on the Total CS:GO site.
  https://totalcsgo.com/commands
'''


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_rcon().put_say_pipein('say {player}: {line}')
