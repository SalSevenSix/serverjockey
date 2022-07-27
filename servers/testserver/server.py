from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs
from core.msg import msgabc, msgext, msgtrf, msgftr
from core.proc import proch, prcext
from core.system import svrabc, svrsvc, svrext
from core.util import util, cmdutil, aggtrf


class Server(svrabc.Server):
    STARTED_FILTER = msgftr.And(
        proch.ServerProcess.FILTER_STDOUT_LINE,
        msgftr.DataStrContains('SERVER STARTED'))

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._pipeinsvc = proch.PipeInLineService(context)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        self._context.register(prcext.ServerStateSubscriber(self._context))
        self._context.register(_ServerDetailsSubscriber(self._context))

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('server', svrext.ServerStatusHandler(self._context)) \
            .append('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER)) \
            .append('{command}', svrext.ServerCommandHandler(self._context)) \
            .pop() \
            .append('log', _ConsoleLogHandler(self._context)) \
            .append('players', _PlayersHandler(self._context)) \
            .push('console') \
            .append('{command}', _ConsoleHandler(self._context)) \
            .pop() \
            .push(self._httpsubs.resource(resource, 'subscriptions')) \
            .append('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await proch.ServerProcess(self._context, 'python3') \
            .append_arg('../projects/serverjockey/servers/testserver/main.py') \
            .use_pipeinsvc(self._pipeinsvc) \
            .wait_for_started(msgext.SingleCatcher(Server.STARTED_FILTER, timeout=60)) \
            .run()

    async def stop(self):
        await proch.PipeInLineService.request(self._context, self, 'quit')


class _ConsoleHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({
        'kick': 'kick {player}'
    })

    def __init__(self, context: contextsvc.Context):
        self._handler = prcext.PipeInLineNoContentPostHandler(context, self, _ConsoleHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class _PlayersHandler(httpabc.AsyncGetHandler):

    def __init__(self, context: contextsvc.Context):
        self._context = context

    async def handle_get(self, resource, data):
        response = await proch.PipeInLineService.request(
            self._context, self, 'players', msgext.MultiCatcher(
                catch_filter=proch.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataStrContains('Players connected'), include_start=False,
                stop_filter=msgftr.DataEquals(''), include_stop=False, timeout=5.0))
        result = []
        if not util.iterable(response):
            return result
        for line in iter([m.data() for m in response]):
            result.append({'steamid': str(util.now_millis()), 'name': line[1:]})
        return result


class _ConsoleLogHandler(httpabc.AsyncGetHandler):

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._subscriber = msgext.RollingLogSubscriber(
            context, size=200,
            msg_filter=msgftr.Or(proch.ServerProcess.FILTER_STDOUT_LINE, proch.ServerProcess.FILTER_STDERR_LINE),
            transformer=msgtrf.GetData(), aggregator=aggtrf.StrJoin('\n'))
        context.register(self._subscriber)

    async def handle_get(self, resource, data):
        return await msgext.RollingLogSubscriber.get_log(self._context, self, self._subscriber.get_identity())


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    INGAMETIME = 'Ingametime'
    INGAMETIME_FILTER = msgftr.DataStrContains(INGAMETIME)

    def __init__(self, mailer: msgabc.MulticastMailer):
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
