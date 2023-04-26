# ALLOW core.* projectzomboid.messaging projectzomboid.playerstore
from core.util import cmdutil, util
from core.msg import msgabc
from core.http import httpabc, httpcnt, httprsc
from core.proc import proch, prcext
from core.common import interceptors
from servers.projectzomboid import playerstore as pls

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
    # 'gunshot': 'gunshot "{player}"',   Doesn't seem to work yet
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
    r.put('steamids', _SteamIdsHandler(mailer))
    r.psh('players', _PlayersHandler(mailer))
    r.psh('x{player}')
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _PLAYER), 's')
    r.pop().pop()
    r.psh('whitelist')
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _WHITELIST), 's')
    r.pop()
    r.psh('banlist')
    r.put('{command}', prcext.ConsoleCommandHandler(mailer, _BANLIST), 's')


class _SteamIdsHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        result = await pls.PlayerStoreService.get(self._mailer, self)
        return result.asdict()


class _PlayersHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        players = await pls.PlayerLoader(self._mailer, self).all()
        return [o.asdict() for o in players]


class _OptionsHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        options = await pls.OptionLoader(self._mailer, self).all()
        return [o.asdict() for o in options]


class _OptionCommandHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({'set': 'changeoption {option} "{value}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        if not await pls.OptionLoader(self._mailer, self).get(util.get('option', data)):
            return httpabc.ResponseBody.NOT_FOUND
        cmdline = _OptionCommandHandler.COMMANDS.get(data)
        if not cmdline or util.get('value', data) is None:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT
