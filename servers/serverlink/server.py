# ALLOW core.* serverlink.*
from core.util import gc, util, logutil, io, aggtrf, objconv
from core.msg import msgtrf, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc, contextext
from core.http import httpabc, httpsubs, httprsc, httpext
from core.system import svrabc, svrext
from core.proc import proch, prcext
from core.common import spstopper

_NO_LOG = 'NO FILE LOGGING. STDOUT ONLY.'
_SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('ServerLink Bot has STARTED'))


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
        self._context, home = context, context.config('home')
        self._config = util.full_path(home, 'serverlink.json')
        self._log_file = util.full_path(home, 'serverlink.log') if logutil.is_logging_to_file() else None
        self._clientfile = contextext.ClientFile(context)
        self._server_factory = _ServerProcessFactory(context, self._config, self._clientfile.path())
        self._stopper = spstopper.ServerProcessStopper(context, 10.0)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        if not await io.file_exists(self._config):
            await io.write_file(self._config, objconv.obj_to_json(_default_config()))
        await self._server_factory.initialise()
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
        r.put('subscribe', self._httpsubs.handler(mc.ServerStatus.UPDATED_FILTER))
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
            await self._server_factory.build().run()
        finally:
            await self._clientfile.delete()

    async def stop(self):
        await self._stopper.stop()


class _ServerProcessFactory:

    def __init__(self, context: contextsvc.Context, config: str, clientfile: str):
        self._context, self._config, self._clientfile = context, config, clientfile
        self._env, self._executable, self._script = None, None, None
        if context.config('scheme') == gc.HTTPS:
            self._env = context.env()
            self._env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

    async def initialise(self):
        env_path = self._context.env('PATH')
        self._executable = self._context.env('HOME') + '/.bun/bin/bun'
        if not await io.file_exists(self._executable):
            self._executable = None
        if not self._executable:
            self._executable = await io.find_in_env_path(env_path, 'bun')
        if not self._executable:
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
        server = proch.ServerProcess(self._context, self._executable)
        server.use_env(self._env)
        server.wait_for_started(_SERVER_STARTED_FILTER, 30.0)
        if self._script:
            server.append_arg(self._script)
        server.append_arg(self._config)
        server.append_arg(self._clientfile)
        return server
