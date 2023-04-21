# ALLOW core.* projectzomboid.*
from core.util import aggtrf
from core.msg import msgtrf
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs, httpext
from core.system import svrabc, svrsvc, svrext
from core.proc import proch, prcext
from servers.projectzomboid import deployment as dep, playerstore as pls, console as con, messaging as msg


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = prcext.ServerProcessStopper(context, 20.0, 'quit')
        self._httpsubs = httpsubs.HttpSubscriptionService(context)
        self._deployment = dep.Deployment(context)
        self._playerstore = pls.PlayerStoreService(context)

    async def initialise(self):
        msg.initialise(self._context)
        self._playerstore.initialise()
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        con.resources(self._context, resource)
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .push('players') \
            .append('subscribe', self._httpsubs.handler(pls.PLAYER_EVENT_FILTER, msgtrf.DataAsDict())) \
            .pop() \
            .push('log') \
            .append('tail', httpext.RollingLogHandler(self._context, msg.CONSOLE_LOG_FILTER)) \
            .append('subscribe', self._httpsubs.handler(msg.CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n'))) \
            .pop() \
            .push(self._httpsubs.resource(resource, 'subscriptions')) \
            .append('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._deployment.new_server_process() \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(msg.SERVER_STARTED_FILTER, 1200) \
            .run()

    async def stop(self):
        await self._stopper.stop()
