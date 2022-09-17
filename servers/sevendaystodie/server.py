from core.context import contextsvc
from core.msg import msgftr
from core.http import httpabc, httprsc
from core.proc import prcext
from core.system import svrabc, svrext
from servers.sevendaystodie import deployment as dep

# INF [EOS] Session address: 121.44.241.224'
# INF [Steamworks.NET] GameServer.LogOn successful, SteamID=90163644755735559, public IP=12*.4*.24*.22*'
SERVER_STARTED_FILTER = msgftr.DataStrContains('INF [Steamworks.NET] GameServer.LogOn successful, SteamID=')


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._stopper = prcext.ServerProcessStopper(context, 20.0, use_interrupt=True)
        self._deployment = dep.Deployment(context)

    async def initialise(self):
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('{command}', svrext.ServerCommandHandler(self._context))

    async def run(self):
        await self._deployment.new_server_process() \
            .wait_for_started(SERVER_STARTED_FILTER, 90) \
            .run()

    async def stop(self):
        await self._stopper.stop()
