# ALLOW core.* unturned.*
from core.util import aggtrf
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.system import svrabc, svrsvc, svrext
from core.proc import prcext, proch
from core.common import playerstore, interceptors
from servers.unturned import deployment as dep, messaging as msg, console as con


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = prcext.ServerProcessStopper(context, 20, 'Shutdown')
        self._deployment = dep.Deployment(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        msg.initialise(self._context)
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        con.resources(self._context, resource)
        r = httprsc.ResourceBuilder(resource)
        r.reg('m', interceptors.block_maintenance_only(self._context))
        r.psh('server', svrext.ServerStatusHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER))
        r.put('{command}', svrext.ServerCommandHandler(self._context), 'm')
        r.pop()
        r.psh('log')
        r.put('tail', httpext.RollingLogHandler(self._context, msg.CONSOLE_LOG_FILTER))
        r.put('subscribe', self._httpsubs.handler(msg.CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n')))
        r.pop()
        r.psh('players', playerstore.PlayersHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(playerstore.PlayersSubscriber.EVENT_FILTER))
        r.pop()
        r.psh(self._httpsubs.resource(resource, 'subscriptions'))
        r.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        server_process = await self._deployment.new_server_process()
        server_process.use_pipeinsvc(self._pipeinsvc)
        server_process.wait_for_started(msg.SERVER_STARTED_FILTER, 90)
        await server_process.run()

    async def stop(self):
        await self._stopper.stop()
