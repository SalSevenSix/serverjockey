from core import httpabc, httpext, proch, msgext, msgtrf, util, aggtrf, cmdutil, msgabc
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
        self._handler = httpext.PipeInLineNoContentPostHandler(mailer, self, WorldCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class OptionsHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return [o.asdict() for o in await ldr.OptionLoader(self._mailer, self, resource).all()]


class OptionsReloadHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({'reload': 'reloadoptions'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = httpext.PipeInLineNoContentPostHandler(mailer, self, OptionsReloadHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, {'command': resource.get_name()})


class OptionCommandHandler(httpabc.DecoderProvider, httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({'set': 'changeoption {option} "{value}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def decoder(self):
        return ldr.OptionLoader.DECODER

    async def handle_post(self, resource, data):
        if not await ldr.OptionLoader(self._mailer, self, resource).get(util.get('option', data)):
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
        playerstore = await subs.CaptureSteamidSubscriber.get_playerstore(self._mailer, self)
        return playerstore.asdict()


class PlayersHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return [o.asdict() for o in await ldr.PlayerLoader(self._mailer, self, resource).all()]


class PlayerCommandHandler(httpabc.DecoderProvider, httpabc.AsyncPostHandler):
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

    def decoder(self):
        return ldr.PlayerLoader.DECODER

    async def handle_post(self, resource, data):
        if not await ldr.PlayerLoader(self._mailer, self, resource).get(util.get('player', data)):
            return httpabc.ResponseBody.NOT_FOUND
        cmdline = PlayerCommandHandler.COMMANDS.get(data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class WhitelistCommandHandler(httpabc.DecoderProvider, httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({
        'add-all': 'addalltowhitelist',
        'add': 'adduser "{player}" "{password}"',
        'remove': 'removeuserfromwhitelist "{player}"'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = httpext.PipeInLineNoContentPostHandler(
            mailer, self, WhitelistCommandHandler.COMMANDS, ldr.PlayerLoader.DECODER)

    def decoder(self):
        return self._handler.decoder()

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class BanlistCommandHandler(httpabc.DecoderProvider, httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({
        'add-player': ['banuser "{player}"', {'ip': '-ip', 'reason': '-r "{}"'}],
        'remove-player': 'unbanuser "{player}"',
        'add-id': 'banid {steamid}',
        'remove-id': 'unbanid {steamid}'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = httpext.PipeInLineNoContentPostHandler(
            mailer, self, BanlistCommandHandler.COMMANDS, ldr.PlayerLoader.DECODER)

    def decoder(self):
        return self._handler.decoder()

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
