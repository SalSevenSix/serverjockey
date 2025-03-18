# ALLOW core.* projectzomboid.*
from core.context import contextsvc
from core.http import httprsc
from core.metrics import mtxinstance
from core.system import svrabc
from core.proc import proch
from core.common import spstopper, restarts, svrhelpers
from servers.projectzomboid import deployment as dep, console as con, messaging as msg, modcheck as mck


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = spstopper.ServerProcessStopper(context, 20.0, 'quit')
        self._deployment = dep.Deployment(context)

    async def initialise(self):
        await mtxinstance.initialise(self._context, error_filter=msg.CONSOLE_LOG_ERROR_FILTER)
        msg.initialise(self._context)
        mck.initialise(self._context)
        await self._deployment.initialise()

    def resources(self, resource: httprsc.WebResource):
        self._deployment.resources(resource)
        con.resources(self._context, resource)
        builder = svrhelpers.ServerResourceBuilder(self._context, resource)
        builder.put_server(restarts.COMMANDS).put_players(no_list=True).put_log(msg.CONSOLE_LOG_FILTER).put_subs()

    async def run(self):
        server = await self._deployment.new_server_process()
        server.use_pipeinsvc(self._pipeinsvc).wait_for_started(msg.SERVER_STARTED_FILTER, 1800)
        await server.run()

    async def stop(self):
        await self._stopper.stop()
