from core import httpabc, proch, prcext, msgext, msgtrf, util, aggtrf, cmdutil, msgabc
from servers.projectzomboid import subscribers as sub, loaders as ldr


class WorldCommandHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({
        'broadcast': 'servermsg "{message}"',
        'save': 'save',
        'chopper': 'chopper',
        'gunshot': 'gunshot',
        'start-rain': 'startrain',
        'stop-rain': 'stoprain'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, WorldCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class OptionsHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        options = await ldr.OptionLoader(self._mailer, self, resource.child('option')).all()
        return [o.asdict() for o in options]


class OptionsReloadHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({'reload': 'reloadoptions'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, OptionsReloadHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, {'command': resource.name()})


class OptionCommandHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({'set': 'changeoption {option} "{value}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        if not await ldr.OptionLoader(self._mailer, self).get(util.get('option', data)):
            return httpabc.ResponseBody.NOT_FOUND
        cmdline = OptionCommandHandler.COMMANDS.get(data)
        if not cmdline or util.get('value', data) is None:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class SteamidsHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpabc.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        playerstore = await sub.CaptureSteamidSubscriber.get_playerstore(self._mailer, self)
        return playerstore.asdict()


class PlayersHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        players = await ldr.PlayerLoader(self._mailer, self, resource.child('player')).all()
        return [o.asdict() for o in players]


class PlayerCommandHandler(httpabc.AsyncPostHandler):
    # LEVELS = ('admin', 'moderator', 'overseer', 'gm', 'observer', 'none')
    COMMANDS = cmdutil.CommandLines({
        'set-access-level': 'setaccesslevel "{player}" "{level}"',
        'give-item': ['additem "{player}" "{module}.{item}"', {'count': '{}'}],
        'spawn-vehicle': 'addvehicle "{module}.{item}" "{player}"',
        'spawn-horde': 'createhorde {count} "{player}"',
        'kick': ['kickuser "{player}"', {'reason': '-r "{}"'}],
        'whitelist': 'addusertowhitelist "{player}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        if not await ldr.PlayerLoader(self._mailer, self).get(util.get('player', data)):
            return httpabc.ResponseBody.NOT_FOUND
        cmdline = PlayerCommandHandler.COMMANDS.get(data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class WhitelistCommandHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({
        'add-all': 'addalltowhitelist',
        'add': 'adduser "{player}" "{password}"',
        'remove': 'removeuserfromwhitelist "{player}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, WhitelistCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class BanlistCommandHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({
        'add-player': ['banuser "{player}"', {'ip': '-ip', 'reason': '-r "{}"'}],
        'remove-player': 'unbanuser "{player}"',
        'add-id': 'banid {steamid}',
        'remove-id': 'unbanid {steamid}'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, BanlistCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class ConsoleLogHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer
        self._subscriber = msgext.RollingLogSubscriber(
            mailer, size=100,
            msg_filter=sub.CONSOLE_LOG_FILTER,
            transformer=msgtrf.GetData(),
            aggregator=aggtrf.StrJoin('\n'))
        mailer.register(self._subscriber)

    async def handle_get(self, resource, data):
        return await msgext.RollingLogSubscriber.get_log(self._mailer, self, self._subscriber.get_identity())
