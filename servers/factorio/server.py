from core.msg import msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc
from core.proc import proch, prcext
from core.system import svrabc, svrext
from servers.factorio import deployment as dep


class Server(svrabc.Server):
    SERVER_STARTED_FILTER = msgftr.And(
        proch.ServerProcess.FILTER_STDOUT_LINE,
        msgftr.DataStrContains('Own address is IP ADDR'))

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._deployment = dep.Deployment(context)

    async def initialise(self):
        self._context.register(prcext.ServerStateSubscriber(self._context))
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('{command}', svrext.ServerCommandHandler(self._context))

    async def run(self):
        await self._deployment.new_server_process() \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(msgext.SingleCatcher(Server.SERVER_STARTED_FILTER, timeout=90)) \
            .run()

    async def stop(self):
        await proch.PipeInLineService.request(self._context, self, '/quit')
