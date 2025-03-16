# ALLOW core.* csii.*
from core.context import contextsvc
from core.http import httpabc
from core.metrics import mtxinstance
from core.system import svrabc
from core.proc import proch
from core.common import spstopper, svrhelpers
from servers.csii import deployment as dep, console as con, messaging as msg

# https://developer.valvesoftware.com/wiki/Counter-Strike_2/Dedicated_Servers


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = spstopper.ServerProcessStopper(context, 10.0, 'quit')
        self._deployment = dep.Deployment(context)

    async def initialise(self):
        await mtxinstance.initialise(self._context)
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
        server.use_pipeinsvc(self._pipeinsvc).wait_for_started(msg.SERVER_STARTED_FILTER, 60.0)
        await server.run()

    async def stop(self):
        await self._stopper.stop()
