# ALLOW core.* serverlink.*
from core.util import util, logutil, io, aggtrf, objconv
from core.msg import msgtrf, msgftr, msglog
from core.context import contextsvc, contextext
from core.http import httpabc, httpsubs, httprsc, httpext
from core.system import svrabc, svrsvc, svrext
from core.proc import proch, prcext

_NO_LOG = 'NO FILE LOGGING. STDOUT ONLY.'
_SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('ServerLink Bot has Started'))


def _default_config():
    return {
        'CMD_PREFIX': '!',
        'ADMIN_ROLE': 'pzadmin',
        'PLAYER_ROLE': 'everyone',
        'BOT_TOKEN': None,
        'EVENT_CHANNELS': {'server': None, 'login': None, 'chat': None},
        'WHITELIST_DM': 'Welcome to our server.\nYour login is ${user} and password is ${pass}'
    }


class Server(svrabc.Server):
    LOG_FILTER = proch.ServerProcess.FILTER_ALL_LINES

    def __init__(self, context: contextsvc.Context):
        home = context.config('home')
        self._context = context
        self._config = util.full_path(home, 'serverlink.json')
        self._log_file = util.full_path(home, 'serverlink.log') if logutil.is_logging_to_file() else None
        self._clientfile = contextext.ClientFile(context, util.full_path(home, 'serverjockey-client.json'))
        self._server_process_factory = _ServerProcessFactory(context, self._config, self._clientfile.path())
        self._stopper = prcext.ServerProcessStopper(context, 10.0)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        if await io.file_exists(self._config):
            await self._migrate_config()
        else:
            await io.write_file(self._config, objconv.obj_to_json(_default_config()))
        await self._server_process_factory.initialise()
        self._context.register(prcext.ServerStateSubscriber(self._context))
        if logutil.is_logging_to_stream():
            self._context.register(msglog.PrintSubscriber(Server.LOG_FILTER, transformer=msgtrf.GetData()))
        if self._log_file:
            await io.write_file(self._log_file, '\n')
            self._context.register(msglog.LogfileSubscriber(
                self._log_file, msg_filter=Server.LOG_FILTER, transformer=msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.psh('server', svrext.ServerStatusHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER))
        r.put('{command}', svrext.ServerCommandHandler(self._context))
        r.pop()
        r.put('config', httpext.FileSystemHandler(self._config))
        r.psh('log', httpext.FileSystemHandler(self._log_file) if self._log_file else httpext.StaticHandler(_NO_LOG))
        r.put('tail', httpext.RollingLogHandler(self._context, Server.LOG_FILTER))
        r.put('subscribe', self._httpsubs.handler(Server.LOG_FILTER, aggtrf.StrJoin('\n')))
        r.pop()
        r.psh(self._httpsubs.resource(resource, 'subscriptions'))
        r.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._clientfile.write()
        try:
            await self._server_process_factory.build().run()
        finally:
            await self._clientfile.delete()

    async def stop(self):
        await self._stopper.stop()

    async def _migrate_config(self):
        # Migration from 0.1.0 to 0.2.0
        update_needed = False
        config = objconv.json_to_dict(await io.read_file(self._config))
        if 'PLAYER_ROLE' not in config:
            update_needed = True
            config['PLAYER_ROLE'] = 'everyone'
        if 'EVENT_CHANNELS' not in config:
            update_needed = True
            cid = config.pop('EVENTS_CHANNEL_ID') if 'EVENTS_CHANNEL_ID' in config else None
            config['EVENT_CHANNELS'] = {'server': cid, 'login': cid, 'chat': cid}
        if update_needed:
            await io.write_file(self._config, objconv.obj_to_json(config))


class _ServerProcessFactory:

    def __init__(self, context: contextsvc.Context, config: str, clientfile: str):
        self._context = context
        self._config = config
        self._clientfile = clientfile
        self._executable, self._script = None, None

    async def initialise(self):
        env_path = self._context.env('PATH')
        self._executable = await io.find_in_env_path(env_path, 'node')
        script = self._context.config('home') + '/index.js'
        if self._executable and await io.file_exists(script):
            self._script = script
            return
        self._executable = self._context.config('home') + '/serverlink'
        if await io.file_exists(self._executable):
            return
        self._executable = await io.find_in_env_path(env_path, 'serverlink')
        if self._executable:
            return
        raise Exception('Unable to find a ServerLink executable.')

    def build(self) -> proch.ServerProcess:
        server_process = proch.ServerProcess(self._context, self._executable)
        server_process.wait_for_started(_SERVER_STARTED_FILTER, 30.0)
        if self._script:
            server_process.append_arg(self._script)
        server_process.append_arg(self._config)
        server_process.append_arg(self._clientfile)
        return server_process
