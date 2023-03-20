import logging
from core.context import contextsvc, contextext
from core.http import httpabc, httpsubs, httprsc, httpext
from core.msg import msgftr, msgtrf, msglog
from core.proc import proch, prcext
from core.system import svrabc, svrsvc, svrext
from core.util import util, logutil, io, aggtrf


class Server(svrabc.Server):

    LOG_FILTER = msgftr.Or(proch.ServerProcess.FILTER_STDOUT_LINE, proch.ServerProcess.FILTER_STDERR_LINE)

    def __init__(self, context: contextsvc.Context):
        home = context.config('home')
        self._context = context
        self._log_file = home + '/serverlink.log'
        self._config = home + '/serverlink.json'
        self._clientfile = contextext.ClientFile(context, home + '/serverjockey-client.json')
        self._server_process_factory = _ServerProcessFactory(context, self._config, self._clientfile.path())
        self._stopper = prcext.ServerProcessStopper(context, 10.0)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        await self._server_process_factory.initialise()
        self._context.register(prcext.ServerStateSubscriber(self._context))
        if logutil.is_logging_to_stream(logging.getLogger()):
            self._context.register(msglog.PrintSubscriber(Server.LOG_FILTER, transformer=msgtrf.GetData()))
        if logutil.is_logging_to_file(logging.getLogger()):
            self._context.register(msglog.LogfileSubscriber(
                self._log_file, Server.LOG_FILTER, transformer=msgtrf.GetData()))
        else:
            await io.write_file(self._log_file, 'NO LOG FILE. STDOUT ONLY.')

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .append('config', httpext.FileSystemHandler(self._config)) \
            .push('log', httpext.FileSystemHandler(self._log_file)) \
            .append('tail', httpext.RollingLogHandler(self._context, Server.LOG_FILTER)) \
            .append('subscribe', self._httpsubs.handler(Server.LOG_FILTER, aggtrf.StrJoin('\n'))) \
            .pop() \
            .push(self._httpsubs.resource(resource, 'subscriptions')) \
            .append('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._clientfile.write()
        try:
            await self._server_process_factory.build().run()
        finally:
            await self._clientfile.delete()

    async def stop(self):
        await self._stopper.stop()


class _ServerProcessFactory:

    def __init__(self, context: contextsvc.Context, config: str, clientfile: str):
        self._context = context
        self._config = config
        self._clientfile = clientfile
        self._executable = None
        self._use_source = False

    async def initialise(self):
        self._executable = self._context.config('home') + '/serverlink'
        if await io.file_exists(self._executable):
            return
        env_path = util.get('PATH', self._context.config('env'))
        self._executable = await io.find_in_env_path(env_path, 'serverlink')
        if self._executable:
            return
        self._executable = await io.find_in_env_path(env_path, 'node')
        if self._executable:
            self._use_source = True
            return
        raise Exception('Unable to find a ServerLink executable.')

    def build(self) -> proch.ServerProcess:
        server_process = proch.ServerProcess(self._context, self._executable)
        if self._use_source:
            server_process.append_arg(self._context.config('home') + '/index.js')
        server_process.append_arg(self._config)
        server_process.append_arg(self._clientfile)
        return server_process
