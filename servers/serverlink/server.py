from core.context import contextsvc
from core.http import httpabc, httpsubs, httprsc, httpext
from core.msg import msgext, msgftr, msgtrf
from core.proc import proch, prcext
from core.system import svrabc, svrsvc, svrext
from core.util import util


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._log = self._context.config('home') + '/serverlink.log'
        self._config = context.config('home') + '/serverlink.json'
        self._clientfile = svrext.ClientFile(context, self._context.config('home') + '/serverjockey-client.json')
        self._server_process_factory = _ServerProcessFactory(context, self._config, self._clientfile.path())
        self._process_subscriber = prcext.ServerProcessSubscriber()
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        await self._server_process_factory.initialise()
        self._context.register(self._process_subscriber)
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
            .append('config', httpext.FileHandler(self._config, True)) \
            .push(self._httpsubs.resource(resource, 'subscriptions')) \
            .append('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._clientfile.write()
        try:
            await self._server_process_factory.build().run()
        finally:
            await self._clientfile.delete()

    async def stop(self):
        self._process_subscriber.terminate_process()


class _ServerProcessFactory:

    def __init__(self, context: contextsvc.Context, config: str, clientfile: str):
        self._context = context
        self._config = config
        self._clientfile = clientfile
        self._executable = '/usr/local/bin/node'
        self._exe_exists = False

    async def initialise(self):
        executable = self._context.config('home') + '/serverlink'
        if await util.file_exists(executable):
            self._executable = executable
            self._exe_exists = True

    def build(self) -> proch.ServerProcess:
        server_process = proch.ServerProcess(self._context, self._executable)
        if not self._exe_exists:
            server_process.append_arg(self._context.config('home') + '/index.js')
        server_process.append_arg(self._config)
        server_process.append_arg(self._clientfile)
        return server_process
