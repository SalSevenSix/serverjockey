# ALLOW core.* hytale.messaging
from core.util import util, cmdutil
from core.msg import msgabc
from core.http import httprsc
from core.proc import prcext
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
    builder.put_help(_HELP_TEXT).put_send_pipein(_HytaleCommandLines()).put_say_pipein(_HytaleSayFormatter())


class _HytaleCommandLines(cmdutil.CommandLines):

    def __init__(self):
        super().__init__(dict(send='{line}'))

    def get(self, args: dict) -> cmdutil.CommandLine | None:
        line = str(util.get('line', args)).lower()
        if line and (line.startswith('update download') or line.startswith('/update download')):
            args['line'] = 'say update download command blocked use Install Runtime in webapp instead'
        return super().get(args)


class _HytaleSayFormatter(prcext.SayFormatter):
    # For some reason Say text must have closing quotes
    def cmdline(self, player: str, line: str) -> str:
        count = line.count("'")
        if count > 0:
            line = line.replace("'ll", '’ll').replace("'m", '’m').replace("'s", '’s')
            line = line.replace("'ve", '’ve').replace("'d", '’d').replace("'t", '’t')
            count = line.count("'")
            if count > 0 and (count % 2) == 1:
                line = line.replace("'", '')
        count = line.count('"')
        if count > 0 and (count % 2) == 1:
            line = line.replace('"', '')
        return f'say {player}: {line}'
