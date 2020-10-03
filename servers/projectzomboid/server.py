from core.util import aggtrf
from core.msg import msgabc, msgext, msgftr, msgtrf
from core.context import contextsvc
from core.http import httpabc, httpext, httpsubs
from core.proc import proch
from core.system import svrabc, svrsvc
from servers.projectzomboid import deployment as dep, playerstore as pls, console as con, messaging as msg


class Server(svrabc.Server):
    STARTED_FILTER = msgftr.And(
        proch.ServerProcess.FILTER_STDOUT_LINE,
        msgftr.DataStrContains('SERVER STARTED'))

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._deployment = dep.Deployment(context)
        self._playerstore = pls.PlayerStoreService(context)
        self._console = con.Console(context)
        self._messaging = msg.Messaging(context)
        self._pipeinsvc = proch.PipeInLineService(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context, context.config('url') + '/subscriptions')

    async def initialise(self):
        self._messaging.initialise()
        self._playerstore.initialise()
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        self._console.resources(resource)
        httpext.ResourceBuilder(resource) \
            .push('server', httpext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', httpext.ServerCommandHandler(self._context)) \
            .pop() \
            .push('log', _ConsoleLogHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(msg.CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n'))) \
            .pop() \
            .push('subscriptions') \
            .append('{identity}', self._httpsubs.subscriptions_handler())

    async def run(self):
        await proch.ServerProcess(self._context, self._deployment.executable()) \
            .append_arg('-cachedir=' + self._deployment.world_dir()) \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(msgext.SingleCatcher(Server.STARTED_FILTER, timeout=60)) \
            .run()   # sync

    async def stop(self):
        await proch.PipeInLineService.request(self._context, self, 'quit')


class _ConsoleLogHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer
        self._subscriber = msgext.RollingLogSubscriber(
            mailer, size=100,
            msg_filter=msg.CONSOLE_LOG_FILTER,
            transformer=msgtrf.GetData(),
            aggregator=aggtrf.StrJoin('\n'))
        mailer.register(self._subscriber)

    async def handle_get(self, resource, data):
        return await msgext.RollingLogSubscriber.get_log(self._mailer, self, self._subscriber.get_identity())
