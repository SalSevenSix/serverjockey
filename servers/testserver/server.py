from collections.abc import Iterable
# ALLOW core.*
from core.util import util, cmdutil, aggtrf
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs, httpext
from core.system import svrabc, svrsvc, svrext
from core.proc import proch, prcext


class Server(svrabc.Server):
    STARTED_FILTER = msgftr.And(
        proch.ServerProcess.FILTER_STDOUT_LINE,
        msgftr.DataStrContains('SERVER STARTED'))
    LOG_FILTER = proch.ServerProcess.FILTER_ALL_LINES

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._python = context.config('python')
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = prcext.ServerProcessStopper(context, 10.0, 'quit')
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        self._context.register(prcext.ServerStateSubscriber(self._context))
        self._context.register(_ServerDetailsSubscriber(self._context))

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .psh('server', svrext.ServerStatusHandler(self._context)) \
            .put('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .put('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .psh('log') \
            .put('tail', httpext.RollingLogHandler(self._context, Server.LOG_FILTER, size=200)) \
            .put('subscribe', self._httpsubs.handler(Server.LOG_FILTER, aggtrf.StrJoin('\n'))) \
            .pop() \
            .put('players', _PlayersHandler(self._context)) \
            .psh('console') \
            .put('{command}', _ConsoleHandler(self._context)) \
            .pop() \
            .psh(self._httpsubs.resource(resource, 'subscriptions')) \
            .put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await proch.ServerProcess(self._context, self._python) \
            .append_arg('../projects/serverjockey/servers/testserver/main.py') \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(Server.STARTED_FILTER, 60) \
            .run()

    async def stop(self):
        await self._stopper.stop()


class _ConsoleHandler(httpabc.PostHandler):
    COMMANDS = cmdutil.CommandLines({
        'kick': 'kick {player}'
    })

    def __init__(self, context: contextsvc.Context):
        self._handler = prcext.ConsoleCommandHandler(context, _ConsoleHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class _PlayersHandler(httpabc.GetHandler):

    def __init__(self, context: contextsvc.Context):
        self._context = context

    async def handle_get(self, resource, data):
        response = await proch.PipeInLineService.request(
            self._context, self, 'players', msgext.MultiCatcher(
                catch_filter=proch.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataStrContains('Players connected'), include_start=False,
                stop_filter=msgftr.DataEquals(''), include_stop=False, timeout=5.0))
        result = []
        if response is None or not isinstance(response, Iterable):
            return result
        for line in [m.data() for m in response]:
            result.append({'steamid': str(util.now_millis()), 'name': line[1:]})
        return result


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    INGAMETIME = 'Ingametime'
    INGAMETIME_FILTER = msgftr.DataStrContains(INGAMETIME)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            _ServerDetailsSubscriber.INGAMETIME_FILTER))
        self._mailer = mailer

    def handle(self, message):
        data = None
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.INGAMETIME)
            data = {'ingametime': value}
        if data:
            svrsvc.ServerStatus.notify_details(self._mailer, self, data)
        return None
