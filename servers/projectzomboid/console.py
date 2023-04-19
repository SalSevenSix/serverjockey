from core.util import cmdutil, util
from core.msg import msgabc
from core.http import httpabc, httpcnt, httprsc
from core.proc import proch, prcext
from servers.projectzomboid import playerstore as pls, domain as dom


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    httprsc.ResourceBuilder(resource) \
        .push('world') \
        .append('{command}', _WorldCommandHandler(mailer)) \
        .pop() \
        .push('config') \
        .push('options', _OptionsHandler(mailer)) \
        .append('reload', _OptionsReloadHandler(mailer)) \
        .push('x{option}') \
        .append('{command}', _OptionCommandHandler(mailer)) \
        .pop().pop().pop() \
        .append('steamids', _SteamidsHandler(mailer)) \
        .push('players', _PlayersHandler(mailer)) \
        .push('x{player}') \
        .append('{command}', _PlayerCommandHandler(mailer)) \
        .pop().pop() \
        .push('whitelist') \
        .append('{command}', _WhitelistCommandHandler(mailer)) \
        .pop() \
        .push('banlist') \
        .append('{command}', _BanlistCommandHandler(mailer))


class _WorldCommandHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({
        'broadcast': 'servermsg "{message}"',
        'save': 'save',
        'chopper': 'chopper',
        'gunshot': 'gunshot',
        'start-storm': 'startstorm',
        'stop-weather': 'stopweather',
        'start-rain': 'startrain',
        'stop-rain': 'stoprain'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, _WorldCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class _OptionsHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        options = await dom.OptionLoader(self._mailer, self, resource.child('option')).all()
        return [o.asdict() for o in options]


class _OptionsReloadHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({'reload': 'reloadoptions'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, _OptionsReloadHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, {'command': resource.name()})


class _OptionCommandHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({'set': 'changeoption {option} "{value}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        if not await dom.OptionLoader(self._mailer, self).get(util.get('option', data)):
            return httpabc.ResponseBody.NOT_FOUND
        cmdline = _OptionCommandHandler.COMMANDS.get(data)
        if not cmdline or util.get('value', data) is None:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class _SteamidsHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        playerstore = await pls.PlayerStoreService.get(self._mailer, self)
        return playerstore.asdict()


class _PlayersHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        players = await dom.PlayerLoader(self._mailer, self, resource.child('player')).all()
        return [o.asdict() for o in players]


class _PlayerCommandHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({
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

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, _PlayerCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        if not await dom.PlayerLoader(self._mailer, self).get(util.get('player', data)):
            return httpabc.ResponseBody.NOT_FOUND
        return await self._handler.handle_post(resource, data)


class _WhitelistCommandHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({
        'add': 'adduser "{player}" "{password}"',
        'remove': 'removeuserfromwhitelist "{player}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, _WhitelistCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class _BanlistCommandHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({
        'add-player': ['banuser "{player}"', {'ip': '-ip', 'reason': '-r "{}"'}],
        'remove-player': 'unbanuser "{player}"',
        'add-id': 'banid {steamid}',
        'remove-id': 'unbanid {steamid}'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, _BanlistCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)
