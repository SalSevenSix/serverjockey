# ALLOW core.* hytale.messaging
from core.msg import msgabc
from core.http import httprsc
from core.common import svrhelpers

_HELP_TEXT = '''HYTALE CONSOLE HELP
Forward slash before commands is optional.
Append --help to any command to learn more.
Command output will be shown in the console log.
More help on commands can be found online.
  https://www.hytalecommands.com/
'''


def resources(mailer: msgabc.MulticastMailer, resource: httprsc.WebResource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_pipein().put_say_pipein('say {player}: {line}')
