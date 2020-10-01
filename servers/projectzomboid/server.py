from core import proch, prcext, msgftr, httpext, svrabc, svrsvc, httpsubs, msgext, aggtrf, msgtrf, contextsvc, httpabc
from servers.projectzomboid import deployment as dep, handlers as hdr, subscribers as sub


class Server(svrabc.Server):
    STARTED_FILTER = msgftr.And(
        proch.Filter.STDOUT_LINE,
        msgftr.DataStrContains('SERVER STARTED'))

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._deployment = dep.Deployment(context)
        self._pipeinsvc = proch.PipeInLineService(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context, context.config('url') + '/subscriptions')
        context.register(prcext.ServerStateSubscriber(context))
        context.register(sub.ServerDetailsSubscriber(context, context.config('host')))
        context.register(sub.CaptureSteamidSubscriber(context))
        context.register(sub.PlayerEventSubscriber(context))
        context.register(sub.ProvideAdminPasswordSubscriber(context, context.config('secret')))

    def resources(self, name: str) -> httpabc.Resource:
        conf_pre = self._deployment.config_dir + '/' + self._deployment.world_name
        return httpext.ResourceBuilder(name) \
            .push('server', httpext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', httpext.ServerCommandHandler(self._context)) \
            .pop() \
            .push('deployment', self._deployment.handler()) \
            .append('{command}', self._deployment.command_handler()) \
            .pop() \
            .push('world') \
            .append('{command}', hdr.WorldCommandHandler(self._context)) \
            .pop() \
            .push('config') \
            .push('options', hdr.OptionsHandler(self._context)) \
            .append('reload', hdr.OptionsReloadHandler(self._context)) \
            .push('x{option}') \
            .append('{command}', hdr.OptionCommandHandler(self._context)) \
            .pop().pop() \
            .append('jvm', httpext.ReadWriteFileHandler(self._deployment.jvm_config_file)) \
            .append('db', httpext.ReadWriteFileHandler(self._deployment.playerdb_file, protected=True, text=False)) \
            .append('ini', httpext.ProtectedLineConfigHandler(conf_pre + '.ini', ('.*Password.*', '.*Token.*'))) \
            .append('sandbox', httpext.ReadWriteFileHandler(conf_pre + '_SandboxVars.lua')) \
            .append('spawnpoints', httpext.ReadWriteFileHandler(conf_pre + '_spawnpoints.lua')) \
            .append('spawnregions', httpext.ReadWriteFileHandler(conf_pre + '_spawnregions.lua')) \
            .pop() \
            .append('steamids', hdr.SteamidsHandler(self._context)) \
            .push('players', hdr.PlayersHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(sub.PlayerEventSubscriber.ALL_FILTER, msgtrf.DataAsDict())) \
            .push('x{player}') \
            .append('{command}', hdr.PlayerCommandHandler(self._context)) \
            .pop().pop() \
            .push('whitelist') \
            .append('{command}', hdr.WhitelistCommandHandler(self._context)) \
            .pop() \
            .push('banlist') \
            .append('{command}', hdr.BanlistCommandHandler(self._context)) \
            .pop() \
            .push('log', hdr.ConsoleLogHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(sub.CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n'))) \
            .pop() \
            .push('subscriptions') \
            .append('{identity}', self._httpsubs.subscriptions_handler()) \
            .pop() \
            .build()

    async def run(self):
        await proch.ProcessHandler(self._context, self._deployment.executable) \
            .append_arg('-cachedir=' + self._deployment.world_dir) \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(msgext.SingleCatcher(Server.STARTED_FILTER, timeout=60)) \
            .run()   # sync

    async def stop(self):
        await proch.PipeInLineService.request(self._context, self, 'quit')
