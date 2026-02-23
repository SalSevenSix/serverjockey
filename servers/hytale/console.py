# ALLOW core.* hytale.messaging
from core.util import util, cmdutil
from core.msg import msgabc, msgftr
from core.http import httprsc
from core.proc import prcext
from core.common import svrhelpers
from servers.hytale import messaging as msg

_HELP_TEXT = '''HYTALE CONSOLE HELP
Forward slash before commands is optional.
Append --help to any command to learn more.
Command output will be shown in the console log.
More help on commands can be found online.
  https://www.hytalecommands.com/
'''

_SEND_COMMANDS = dict(send='{line}')
_PERM_COMMANDS = dict(
    add='perm user group add {player} {group}',
    remove='perm user group remove {player} {group}')


class Console:

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer
        self._uuid_service = _UuidService()

    def initialise(self):
        self._mailer.register(self._uuid_service)

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.ConsoleResourceBuilder(self._mailer, resource).psh_console()
        builder.put_help(_HELP_TEXT).put_send_pipein(_SendCommandLines()).put_say_pipein(_SayFormatter())
        builder.psh('perm').psh('players').psh('x{player}').psh('groups')
        builder.put('{command}', prcext.ConsoleCommandHandler(
            self._mailer, _UuidCommandLines(_PERM_COMMANDS, self._uuid_service)), 's')


class _UuidService(msgabc.AbcSubscriber):

    def __init__(self):
        super().__init__(msgftr.NameIs(msg.USER_UUID))
        self._name_to_uuid = {}

    def handle(self, message):
        uuid, name = message.data()
        if uuid and name:
            self._name_to_uuid[name] = uuid

    def lookup_uuid(self, name: str | None) -> str | None:
        return util.get(name, self._name_to_uuid)


class _UuidCommandLines(cmdutil.CommandLines):

    def __init__(self, commands: dict, uuid_service: _UuidService):
        super().__init__(commands)
        self._uuid_service = uuid_service

    def get(self, args: dict) -> cmdutil.CommandLine | None:
        player = self._uuid_service.lookup_uuid(util.get('player', args))
        if player:
            args['player'] = player
        return super().get(args)


class _SendCommandLines(cmdutil.CommandLines):

    def __init__(self):
        super().__init__(_SEND_COMMANDS)

    def get(self, args: dict) -> cmdutil.CommandLine | None:
        line = str(util.get('line', args)).lower()
        if line and (line.startswith('update download') or line.startswith('/update download')):
            args['line'] = 'say update download command blocked use Install Runtime in webapp instead'
        return super().get(args)


class _SayFormatter(prcext.SayFormatter):
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
