from core.context import contextsvc, contextext
from core.http import httpabc, httpsubs, httprsc, httpext
from core.msg import msgext, msgftr, msgtrf
from core.proc import proch, prcext
from core.system import svrabc, svrsvc, svrext
from core.util import io


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        home = context.config('home')
        self._context = context
        self._log = home + '/serverlink.log'
        self._config = home + '/serverlink.json'
        self._clientfile = contextext.ClientFile(context, home + '/serverjockey-client.json')
        self._server_process_factory = _ServerProcessFactory(context, self._config, self._clientfile.path())
        self._stopper = prcext.ServerProcessStopper(context, 10.0)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        await self._server_process_factory.initialise()
        self._context.register(prcext.ServerStateSubscriber(self._context))
        self._context.register(msgext.LogfileSubscriber(
            self._log,
            msgftr.Or(proch.ServerProcess.FILTER_STDOUT_LINE, proch.ServerProcess.FILTER_STDERR_LINE),
            msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .append('config', httpext.FileSystemHandler(self._config)) \
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
        self._executable = '/usr/local/bin/node'
        self._exe_exists = False

    async def initialise(self):
        alternates = [self._context.config('home') + '/serverlink', '/usr/local/bin/serverlink']
        for executable in alternates:
            if await io.file_exists(executable):
                self._executable = executable
                self._exe_exists = True
                return

    def build(self) -> proch.ServerProcess:
        server_process = proch.ServerProcess(self._context, self._executable)
        if not self._exe_exists:
            server_process.append_arg(self._context.config('home') + '/index.js')
        server_process.append_arg(self._config)
        server_process.append_arg(self._clientfile)
        return server_process
