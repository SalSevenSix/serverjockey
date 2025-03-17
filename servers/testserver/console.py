# ALLOW core.* testserver.messaging
from core.msg import msgabc
from core.http import httpabc
from core.common import svrhelpers

_HELP_TEXT = '''CONSOLE COMMANDS
quit, crash, players,
login {player}, logout {player},
say {player} {text}, kill {player},
broadcast {message}, error {message},
restart-warnings, restart-empty
load {processors} {seconds}
'''


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_pipein()
