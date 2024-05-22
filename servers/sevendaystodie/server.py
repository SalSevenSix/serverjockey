# ALLOW core.* sevendaystodie.*
from core.util import aggtrf
from core.msgc import mc
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.system import svrabc, svrext
from core.common import playerstore, interceptors, spstopper
from servers.sevendaystodie import deployment as dep, messaging as msg


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._stopper = spstopper.ServerProcessStopper(context, 20.0, use_interrupt=True)
        self._deployment = dep.Deployment(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        msg.initialise(self._context)
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        r = httprsc.ResourceBuilder(resource)
        r.reg('m', interceptors.block_maintenance_only(self._context))
        r.psh('server', svrext.ServerStatusHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(mc.ServerStatus.UPDATED_FILTER))
        r.put('{command}', svrext.ServerCommandHandler(self._context), 'm')
        r.pop()
        r.psh('log')
        r.put('tail', httpext.RollingLogHandler(self._context, msg.CONSOLE_LOG_FILTER))
        r.put('subscribe', self._httpsubs.handler(msg.CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n')))
        r.pop()
        r.psh('players', playerstore.PlayersHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(mc.PlayerStore.EVENT_FILTER, mc.PlayerStore.EVENT_TRF))
        r.pop()
        r.psh(self._httpsubs.resource(resource, 'subscriptions'))
        r.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        server_process = await self._deployment.new_server_process()
        await server_process.wait_for_started(msg.SERVER_STARTED_FILTER, 300).run()

    async def stop(self):
        await self._stopper.stop()
