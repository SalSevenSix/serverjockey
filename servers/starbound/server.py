# ALLOW core.* starbound.*
from core.context import contextsvc
from core.http import httpabc
from core.metrics import mtxinstance
from core.system import svrabc
from core.common import spstopper, svrhelpers
from servers.starbound import deployment as dep, messaging as msg, console as con


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._stopper = spstopper.ServerProcessStopper(context, 20.0, use_interrupt=True)
        self._deployment = dep.Deployment(context)

    async def initialise(self):
        await mtxinstance.initialise(self._context, error_filter=msg.CONSOLE_LOG_ERROR_FILTER)
        con.initialise(self._context)
        await msg.initialise(self._context)
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        con.resources(self._context, resource)
        self._deployment.resources(resource)
        builder = svrhelpers.ServerResourceBuilder(self._context, resource)
        builder.put_server().put_players().put_log(msg.CONSOLE_LOG_FILTER).put_subs()

    async def run(self):
        server = await self._deployment.new_server_process()
        server.wait_for_started(msg.SERVER_STARTED_FILTER, 60)
        await server.run()

    async def stop(self):
        await self._stopper.stop()
