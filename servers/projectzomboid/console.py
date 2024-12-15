import typing
from collections.abc import Iterable
# ALLOW core.* projectzomboid.messaging projectzomboid.playerstore
from core.util import cmdutil, util
from core.msg import msgabc, msgext, msgftr
from core.msgc import mc
from core.http import httpabc, httprsc, httpsec
from core.proc import proch, prcext
from core.common import interceptors, playerstore

_OPTIONS_RELOAD = cmdutil.CommandLines({'reload': 'reloadoptions'})
_WORLD = cmdutil.CommandLines({
    'broadcast': 'servermsg "{message}"',
    'save': 'save',
    'chopper': 'chopper',
    'gunshot': 'gunshot',
    'start-storm': 'startstorm',
    'stop-weather': 'stopweather',
    'start-rain': 'startrain',
    'stop-rain': 'stoprain'})
_PLAYER = cmdutil.CommandLines({
    'set-access-level': 'setaccesslevel "{player}" "{level}"',
    'give-item': ['additem "{player}" "{module}.{item}"', {'count': '{}'}],
    'give-xp': 'addxp "{player}" {skill}={xp}',
    'spawn-vehicle': 'addvehicle "{module}.{item}" "{player}"',
    'spawn-horde': 'createhorde {count} "{player}"',
    'tele-to': 'teleport "{player}" "{toplayer}"',
    'tele-at': 'teleportto "{player}" {location}',
    'lightning': 'lightning "{player}"',
    'thunder': 'thunder "{player}"',
    'kick': ['kickuser "{player}"', {'reason': '-r "{}"'}]})
_WHITELIST = cmdutil.CommandLines({
    'add': 'adduser "{player}" "{password}"',
    'remove': 'removeuserfromwhitelist "{player}"'})
_BANLIST = cmdutil.CommandLines({
    'add-player': ['banuser "{player}"', {'ip': '-ip', 'reason': '-r "{}"'}],
    'remove-player': 'unbanuser "{player}"',
    'add-id': 'banid {steamid}',
    'remove-id': 'unbanid {steamid}'})


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('world')
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _WORLD), 's')
    r.pop()
    r.psh('config')
    r.psh('options', _OptionsHandler(mailer), 's')
    r.put('reload', prcext.ConsoleCommandHandler(mailer, _OPTIONS_RELOAD), 's')
    r.psh('x{option}')
    r.put('{command}', _OptionCommandHandler(mailer), 's')
    r.pop().pop().pop()
    r.psh('players', _PlayersHandler(mailer))
    r.psh('x{player}')
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _PLAYER), 's')
    r.pop().pop()
    r.psh('whitelist')
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _WHITELIST), 's')
    r.pop()
    r.psh('banlist')
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _BANLIST), 's')


class _PlayersHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        response = await proch.PipeInLineService.request(
            self._mailer, self, 'players', msgext.MultiCatcher(
                catch_filter=mc.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataStrContains('Players connected'), include_start=False,
                stop_filter=msgftr.DataEquals(''), include_stop=False,
                timeout=10.0))
        players = []
        if response is None or not isinstance(response, Iterable):
            return players
        for line in [m.data() for m in response]:
            if line.startswith('-'):
                players.append(playerstore.Player(line[1:], ''))
        return await playerstore.PlayersSubscriber.get(self._mailer, self, players)


class _OptionsHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        options = await _OptionLoader(self._mailer, self).all()
        return [o.asdict() for o in options]


class _OptionCommandHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({'set': 'changeoption {option} "{value}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        if not await _OptionLoader(self._mailer, self).get(util.get('option', data)):
            return httpabc.ResponseBody.NOT_FOUND
        cmdline = _OptionCommandHandler.COMMANDS.get(data)
        if not cmdline or util.get('value', data) is None:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class _Option:

    def __init__(self, option: str, value: str):
        self._data = {'option': option, 'value': value}

    def option(self) -> str:
        return self._data['option']

    def asdict(self) -> dict:
        return self._data.copy()


class _OptionLoader:

    def __init__(self, mailer: msgabc.MulticastMailer, source: typing.Any):
        self._mailer = mailer
        self._source = source

    async def all(self) -> typing.Collection[_Option]:
        response = await proch.PipeInLineService.request(
            self._mailer, self._source, 'showoptions', msgext.MultiCatcher(
                catch_filter=mc.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataStrContains('List of Server Options:'), include_start=False,
                stop_filter=msgftr.DataStrContains('ServerWelcomeMessage'), include_stop=True,
                timeout=10.0))
        options = []
        if response is None or not isinstance(response, Iterable):
            return options
        for line in [m.data() for m in response]:
            if line.startswith('* '):
                option, value = line[2:].split('=')
                options.append(_Option(option, value))
        return options

    async def get(self, option: str) -> typing.Optional[_Option]:
        if option is None:
            return None
        options = [o for o in await self.all() if o.option() == option]
        return util.single(options)
