# ALLOW core.* unturned.messaging
from core.msg import msgabc
from core.http import httprsc
from core.common import svrhelpers

_HELP_TEXT = '''UNTURNED CONSOLE HELP
Use Help to see list of commands. 
Use Help {command} to get detailed information.
Command output will be shown in the console log.
More help on commands can be found on the wiki.
  https://unturned.fandom.com/wiki/Server_Commands
'''


def resources(mailer: msgabc.MulticastMailer, resource: httprsc.WebResource):
    builder = svrhelpers.ConsoleResourceBuilder(mailer, resource).psh_console()
    builder.put_help(_HELP_TEXT).put_send_pipein().put_say_pipein('Say {player}: {line}')
