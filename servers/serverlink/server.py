# ALLOW core.* serverlink.*
from core.util import gc, util, logutil, io, aggtrf, objconv
from core.msg import msgtrf, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc, contextext
from core.http import httpsubs, httprsc, httpext
from core.metrics import mtxinstance
from core.system import svrabc, svrext
from core.proc import proch, prcext
from core.common import spstopper

_NO_LOG = 'NO FILE LOGGING. STDOUT ONLY.'
_LOG_FILTER = mc.ServerProcess.FILTER_ALL_LINES
_ERROR_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.DataMatches(r'^\d{4}-[01]\d-[0-3]\d [0-2]\d:[0-5]\d:[0-5]\d ERROR.*'))
_SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('ServerLink Bot has STARTED'))


def _migrate_config(config) -> dict:
    element = util.get('LLM_API', config)
    if element:
        element = util.get('chatlog', element)
        if element:
            element = util.get('messages', element)
            if element:
                del config['LLM_API']
    return config


def _default_config() -> dict:
    clsys = 'You are a helpful assistant that summarizes conversations concisely.'
    clusr = ('Summarize the following transcript between players in the game \'{gamename}\'.'
             ' Identify separate conversations and provide a brief summary of each.'
             ' Each summary should include the names of all the players involved.'
             ' Ignore messages from players that do not have any responses from other players.'
             ' Do not include a Key Points section, just provide conversation summaries.'
             '\n\n{content}')
    cbsys = ('You are a helpful assistant with expert knowledge about the game \'{gamename}\'.'
             ' You will answer questions strictly based on the game lore, mechanics, and world.'
             ' Keep the responses concise unless asked otherwise.'
             ' If a question is outside of {gamename}, politely say you cannot help.')
    return {
        'BOT_TOKEN': None, 'CMD_PREFIX': '!',
        'ADMIN_ROLE': '@admin', 'PLAYER_ROLE': '@everyone',
        'EVENT_CHANNELS': {'server': None, 'login': None, 'chat': None},
        'WHITELIST_DM': 'Welcome to the {instance} server.\nYour login is `{user}` and password is `{pass}`',
        'LLM_API': {
            'baseurl': None, 'apikey': None,
            'chatlog': {'model': None, 'temperature': None, 'maxtokens': None, 'system': clsys, 'user': clusr},
            'chatbot': {'model': None, 'temperature': None, 'maxtokens': None, 'system': cbsys}
        }
    }


class Server(svrabc.Server):

    def __init__(self, context: contextsvc.Context):
        self._context, home = context, context.config('home')
        self._config = util.full_path(home, 'serverlink.json')
        self._log_file = util.full_path(home, 'serverlink.log') if logutil.is_logging_to_file() else None
        self._clientfile = contextext.ClientFile(context)
        self._server_factory = _ServerProcessFactory(context, self._config, self._clientfile.path())
        self._stopper = spstopper.ServerProcessStopper(context, 10.0)
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        await io.keyfill_json_file(self._config, _default_config(), _migrate_config)
        await self._server_factory.initialise()
        await mtxinstance.initialise(self._context, players=False, error_filter=_ERROR_FILTER)
        self._context.register(prcext.ServerStateSubscriber(self._context))
        if logutil.is_logging_to_stream():
            self._context.register(msglog.PrintSubscriber(_LOG_FILTER, transformer=msgtrf.GetData()))
        if self._log_file:
            await io.write_file(self._log_file, '\n')
            self._context.register(msglog.LogfileSubscriber(
                self._log_file, msg_filter=_LOG_FILTER, transformer=msgtrf.GetData()))

    def resources(self, resource: httprsc.WebResource):
        builder = httprsc.ResourceBuilder(resource)
        builder.psh('server', svrext.ServerStatusHandler(self._context))
        builder.put('subscribe', self._httpsubs.handler(mc.ServerStatus.UPDATED_FILTER))
        builder.put('{command}', svrext.ServerCommandHandler(self._context))
        builder.pop()
        log_handler = httpext.FileSystemHandler(self._log_file) if self._log_file else httpext.StaticHandler(_NO_LOG)
        builder.psh('log', log_handler)
        builder.put('tail', httpext.RollingLogHandler(self._context, _LOG_FILTER))
        builder.put('subscribe', self._httpsubs.handler(_LOG_FILTER, aggtrf.StrJoin('\n')))
        builder.pop()
        builder.put('config', httpext.FileSystemHandler(self._config))
        builder.psh(self._httpsubs.resource(resource, 'subscriptions'))
        builder.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        await self._clientfile.write()
        try:
            await self._server_factory.build().run()
        finally:
            await self._clientfile.delete()

    async def stop(self):
        await self._stopper.stop()


class _ServerProcessFactory:

    def __init__(self, context: contextsvc.Context, config: str, clientfile: str):
        self._context, self._config, self._clientfile = context, config, clientfile
        self._env, self._executable, self._script = None, None, None
        if context.config('scheme') == gc.HTTPS:
            self._env = context.env()
            self._env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

    async def initialise(self):
        self._executable = self._context.config('home') + '/serverlink'
        if await io.file_exists(self._executable):
            return
        env_path = self._context.env('PATH')
        script = self._context.config('home') + '/index.js'
        if await io.file_exists(script):
            self._executable = self._context.env('HOME') + '/.bun/bin/bun'
            if not await io.file_exists(self._executable):
                self._executable = None
            if not self._executable:
                self._executable = await io.find_in_env_path(env_path, 'bun')
            if not self._executable:
                self._executable = await io.find_in_env_path(env_path, 'node')
            if self._executable:
                self._script = script
                return
        self._executable = await io.find_in_env_path(env_path, 'serverlink')
        if self._executable:
            return
        raise Exception('Unable to find a ServerLink executable.')

    def build(self) -> proch.ServerProcess:
        server = proch.ServerProcess(self._context, self._executable)
        server.use_env(self._env)
        server.wait_for_started(_SERVER_STARTED_FILTER, 30.0)
        if self._script:
            server.append_arg(self._script)
        server.append_arg(self._config)
        server.append_arg(self._clientfile)
        return server
