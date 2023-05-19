# ALLOW core.* starbound.*
from core.util import aggtrf
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs, httpext
from core.system import svrabc, svrsvc, svrext
from core.proc import prcext
from core.common import playerstore, interceptors
from servers.starbound import deployment as dep, messaging as msg, console as con


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._stopper = prcext.ServerProcessStopper(context, 20.0, use_interrupt=True)
        self._deployment = dep.Deployment(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        await msg.initialise(self._mailer)
        await con.initialise(self._mailer)
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        con.resources(self._mailer, resource)
        self._deployment.resources(resource)
        r = httprsc.ResourceBuilder(resource)
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('server', svrext.ServerStatusHandler(self._mailer))
        r.put('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER))
        r.put('{command}', svrext.ServerCommandHandler(self._mailer), 'm')
        r.pop()
        r.psh('log')
        r.put('tail', httpext.RollingLogHandler(self._mailer, msg.CONSOLE_LOG_FILTER))
        r.put('subscribe', self._httpsubs.handler(msg.CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n')))
        r.pop()
        r.psh('players', playerstore.PlayersHandler(self._mailer))
        r.put('subscribe', self._httpsubs.handler(playerstore.PlayersSubscriber.EVENT_FILTER))
        r.pop()
        r.psh(self._httpsubs.resource(resource, 'subscriptions'))
        r.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        server_process = await self._deployment.new_server_process()
        server_process.wait_for_started(msg.SERVER_STARTED_FILTER, 60)
        await server_process.run()

    async def stop(self):
        await self._stopper.stop()
