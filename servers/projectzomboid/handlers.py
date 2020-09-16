from core import httpsvc, httpext, proch, msgext, msgtrf, util, aggtrf, cmdutil
from servers.projectzomboid import subscribers as s, domain as d


class DeploymentHandler:

    def __init__(self, deployment):
        self.deployment = deployment

    async def handle_get(self, resource, data):
        return self.deployment.directory_list()


class DeploymentCommandHandler:
    DECODER = httpext.DictionaryCoder().append('beta', util.script_escape)

    def __init__(self, deployment):
        self.deployment = deployment

    def get_decoder(self):
        return DeploymentCommandHandler.DECODER

    async def handle_post(self, resource, data):
        command = util.get('command', data)
        if command == 'backup-world':
            return {'file': self.deployment.backup_world()}
        if command == 'wipe-world-all':
            self.deployment.wipe_world_all()
            return httpsvc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-playerdb':
            self.deployment.wipe_world_playerdb()
            return httpsvc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-config':
            self.deployment.wipe_world_config()
            return httpsvc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-save':
            self.deployment.wipe_world_save()
            return httpsvc.ResponseBody.NO_CONTENT
        if command == 'backup-runtime':
            return {'file': self.deployment.backup_runtime()}
        if command == 'install-runtime':
            return await self.deployment.install_runtime(
                beta=util.get('beta', data),
                validate=util.get('validate', data))
        return httpsvc.ResponseBody.NOT_FOUND


class WorldCommandHandler:
    COMMANDS = cmdutil.CommandLines({
        'broadcast': 'servermsg "{message}"',
        'save': 'save',
        'chopper': 'chopper',
        'gunshot': 'gunshot',
        'start-rain': 'startrain',
        'stop-rain': 'stoprain'})

    def __init__(self, context):
        self.handler = httpext.PipeInLineNoContentPostHandler(
            context, self, WorldCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self.handler.handle_post(resource, data)


class OptionsHandler:

    def __init__(self, mailer):
        self.mailer = mailer

    async def handle_get(self, resource, data):
        return [o.get_data() for o in await d.Option.Loader(self.mailer, self, resource).all()]


class OptionsReloadHandler:
    COMMANDS = cmdutil.CommandLines({'reload': 'reloadoptions'})

    def __init__(self, mailer):
        self.handler = httpext.PipeInLineNoContentPostHandler(
            mailer, self, OptionsReloadHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self.handler.handle_post(resource, {'command': resource.get_name()})


class OptionCommandHandler:
    COMMANDS = cmdutil.CommandLines({'set': 'changeoption {option} "{value}"'})

    def __init__(self, mailer):
        self.mailer = mailer

    def get_decoder(self):
        return d.Option.DECODER

    async def handle_post(self, resource, data):
        if not await d.Option.Loader(self.mailer, self, resource).get(util.get('option', data)):
            return httpsvc.ResponseBody.NOT_FOUND
        cmdline = OptionCommandHandler.COMMANDS.get(data)
        if not cmdline or util.get('value', data) is None:
            return httpsvc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self.mailer, self, cmdline.build())
        return httpsvc.ResponseBody.NO_CONTENT


class SteamidsHandler:

    def __init__(self, mailer):
        self.mailer = mailer
        mailer.register(s.CaptureSteamidSubscriber(mailer))

    async def handle_get(self, resource, data):
        return await s.CaptureSteamidSubscriber.request(self.mailer, self)


class PlayersHandler:

    def __init__(self, mailer):
        self.mailer = mailer

    async def handle_get(self, resource, data):
        return [p.get_data() for p in await d.Player.Loader(self.mailer, self, resource).all()]


class PlayerCommandHandler:
    # LEVELS = ('admin', 'moderator', 'overseer', 'gm', 'observer', 'none')
    COMMANDS = cmdutil.CommandLines({
        'set-access-level': 'setaccesslevel "{player}" "{level}"',
        'give-item': ['additem "{player}" "{module}.{item}"', {'count': '{}'}],
        'spawn-vehicle': 'addvehicle "{module}.{item}" "{player}"',
        'spawn-horde': 'createhorde {count} "{player}"',
        'kick': ['kickuser "{player}"', {'reason': '-r "{}"'}],
        'whitelist': 'addusertowhitelist "{player}"'})

    def __init__(self, mailer):
        self.mailer = mailer

    def get_decoder(self):
        return d.Player.DECODER

    async def handle_post(self, resource, data):
        if not await d.Player.Loader(self.mailer, self, resource).get(util.get('player', data)):
            return httpsvc.ResponseBody.NOT_FOUND
        cmdline = PlayerCommandHandler.COMMANDS.get(data)
        if not cmdline:
            return httpsvc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self.mailer, self, cmdline.build())
        return httpsvc.ResponseBody.NO_CONTENT


class WhitelistCommandHandler:
    COMMANDS = cmdutil.CommandLines({
        'add-all': 'addalltowhitelist',
        'add': 'adduser "{player}" "{password}"',
        'remove': 'removeuserfromwhitelist "{player}"'})

    def __init__(self, mailer):
        self.handler = httpext.PipeInLineNoContentPostHandler(
            mailer, self, WhitelistCommandHandler.COMMANDS, d.Player.DECODER)

    def get_decoder(self):
        return self.handler.get_decoder()

    async def handle_post(self, resource, data):
        return await self.handler.handle_post(resource, data)


class BanlistCommandHandler:
    COMMANDS = cmdutil.CommandLines({
        'add-player': ['banuser "{player}"', {'ip': '-ip', 'reason': '-r "{}"'}],
        'remove-player': 'unbanuser "{player}"',
        'add-id': 'banid {steamid}',
        'remove-id': 'unbanid {steamid}'})

    def __init__(self, mailer):
        self.handler = httpext.PipeInLineNoContentPostHandler(
            mailer, self, BanlistCommandHandler.COMMANDS, d.Player.DECODER)

    def get_decoder(self):
        return self.handler.get_decoder()

    async def handle_post(self, resource, data):
        return await self.handler.handle_post(resource, data)


class ConsoleLogHandler:
    FILTER = s.ConsoleLogFilter()

    def __init__(self, mailer):
        self.mailer = mailer
        self.subscriber = msgext.RollingLogSubscriber(
            mailer, size=100,
            msg_filter=ConsoleLogHandler.FILTER,
            transformer=msgtrf.GetData(),
            aggregator=aggtrf.StrJoin('\n'))
        mailer.register(self.subscriber)

    async def handle_get(self, resource, data):
        return await msgext.RollingLogSubscriber.request(self.mailer, self, self.subscriber.get_identity())
