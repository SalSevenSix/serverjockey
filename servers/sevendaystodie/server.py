# ALLOW core.* sevendaystodie.*
from core.util import aggtrf
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.system import svrabc, svrsvc, svrext
from core.proc import prcext
from core.common import playerstore
from servers.sevendaystodie import deployment as dep, messaging as msg


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._stopper = prcext.ServerProcessStopper(context, 20.0, use_interrupt=True)
        self._deployment = dep.Deployment(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        msg.initialise(self._context)
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        httprsc.ResourceBuilder(resource) \
            .psh('server', svrext.ServerStatusHandler(self._context)) \
            .put('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .put('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .psh('log') \
            .put('tail', httpext.RollingLogHandler(self._context, msg.CONSOLE_LOG_FILTER)) \
            .put('subscribe', self._httpsubs.handler(msg.CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n'))) \
            .pop() \
            .psh('players', playerstore.PlayersHandler(self._context)) \
            .put('subscribe', self._httpsubs.handler(playerstore.PlayersSubscriber.EVENT_FILTER)) \
            .pop() \
            .psh(self._httpsubs.resource(resource, 'subscriptions')) \
            .put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._deployment.build_live_config()
        await self._deployment.new_server_process() \
            .wait_for_started(msg.SERVER_STARTED_FILTER, 120) \
            .run()

    async def stop(self):
        await self._stopper.stop()
