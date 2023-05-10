# ALLOW core.* starbound.*
from core.util import aggtrf
from core.msg import msgftr, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs, httpext
from core.system import svrabc, svrsvc, svrext
from core.proc import proch, prcext, jobh
from servers.starbound import deployment as dep

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('[Info] Root: Writing runtime configuration to'))
CONSOLE_LOG_FILTER = msgftr.Or(
    proch.ServerProcess.FILTER_ALL_LINES,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.LoggingPublisher.FILTER_ALL_LEVELS)


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._stopper = prcext.ServerProcessStopper(context, 20.0, use_interrupt=True)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)
        self._deployment = dep.Deployment(context)

    async def initialise(self):
        await self._deployment.initialise()

    def resources(self, resource: httpabc.Resource):
        self._deployment.resources(resource)
        r = httprsc.ResourceBuilder(resource)
        r.psh('server', svrext.ServerStatusHandler(self._mailer))
        r.put('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER))
        r.put('{command}', svrext.ServerCommandHandler(self._mailer))
        r.pop()
        r.psh('log')
        r.put('tail', httpext.RollingLogHandler(self._mailer, CONSOLE_LOG_FILTER))
        r.put('subscribe', self._httpsubs.handler(CONSOLE_LOG_FILTER, aggtrf.StrJoin('\n')))
        r.pop()
        r.psh(self._httpsubs.resource(resource, 'subscriptions'))
        r.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._deployment.new_server_process() \
            .wait_for_started(SERVER_STARTED_FILTER, 60) \
            .run()

    async def stop(self):
        await self._stopper.stop()
