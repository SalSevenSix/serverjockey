# ALLOW core.* barotrauma.*
from core.msg import msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs
from core.system import svrabc, svrext, svrsvc
from core.proc import proch, prcext
from servers.barotrauma import deployment as dep

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('Server started'))


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = prcext.ServerProcessStopper(context, 20.0, 'exit')
        self._deployment = dep.Deployment(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        await self._deployment.initialise()
        self._context.register(prcext.ServerStateSubscriber(self._context))

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .push(self._httpsubs.resource(resource, 'subscriptions')) \
            .append('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._deployment.new_server_process() \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(SERVER_STARTED_FILTER, 60) \
            .run()

    async def stop(self):
        await self._stopper.stop()
