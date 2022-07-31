from core.util import aggtrf
from core.msg import msgabc, msgftr, msgtrf, msgext
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs
from core.proc import proch
from core.system import svrabc, svrsvc, svrext
from servers.factorio import deployment as dep, messaging as msg, playerstore as pls


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._deployment = dep.Deployment(context)
        self._messaging = msg.Messaging(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        self._context.register(pls.PlayersSubscriber(self._context))
        self._messaging.initialise()
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .push('players', pls.PlayersHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(msg.PLAYER_EVENT_FILTER)) \
            .pop() \
            .push('log') \
            .append('tail', _ConsoleLogHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(_ConsoleLogHandler.FILTER, aggtrf.StrJoin('\n'))) \
            .pop() \
            .push(self._httpsubs.resource(resource, 'subscriptions')) \
            .append('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._deployment.ensure_map()
        await self._deployment.new_server_process() \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(msgext.SingleCatcher(msg.SERVER_STARTED_FILTER, timeout=90)) \
            .run()

    async def stop(self):
        await proch.PipeInLineService.request(self._context, self, '/quit')


class _ConsoleLogHandler(httpabc.AsyncGetHandler):
    FILTER = msgftr.Or(proch.ServerProcess.FILTER_STDOUT_LINE, proch.ServerProcess.FILTER_STDERR_LINE)

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer
        self._subscriber = msgext.RollingLogSubscriber(
            mailer, size=100,
            msg_filter=_ConsoleLogHandler.FILTER,
            transformer=msgtrf.GetData(),
            aggregator=aggtrf.StrJoin('\n'))
        mailer.register(self._subscriber)

    async def handle_get(self, resource, data):
        return await msgext.RollingLogSubscriber.get_log(self._mailer, self, self._subscriber.get_identity())
