from collections.abc import Iterable
# ALLOW core.*
from core.util import util, dtutil, objconv, io, cmdutil, aggtrf, pkg
from core.msg import msgabc, msgext, msgftr, msglog, msgtrf
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs, httpext
from core.system import svrabc, svrsvc, svrext
from core.proc import proch, prcext
from core.common import interceptors, playerstore

_MAIN_PY = 'main.py'
_COMMANDS = cmdutil.CommandLines({'send': '{line}'})
_COMMANDS_HELP_TEXT = '''CONSOLE COMMANDS
players     say {player} {text}
quit        login {player}
crash       logout {player}
'''

MAINTENANCE_STATE_FILTER = msgftr.Or(msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


def _default_config():
    return {
        'start_speed_modifier': 1,
        'crash_on_start_seconds': 0.0,
        'ingametime_interval_seconds': 80.0
    }


class Server(svrabc.Server):
    STARTED_FILTER = msgftr.And(
        proch.ServerProcess.FILTER_STDOUT_LINE,
        msgftr.DataStrContains('SERVER STARTED'))
    LOG_FILTER = proch.ServerProcess.FILTER_ALL_LINES

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._python = context.config('python')
        self._home_dir, self._tmp_dir = context.config('home'), context.config('tmpdir')
        self._config_file = self._home_dir + '/config.json'
        self._backups_dir = self._home_dir + '/backups'
        self._log_dir = self._home_dir + '/logs'
        self._runtime_dir = self._home_dir + '/runtime'
        self._executable = self._runtime_dir + '/' + _MAIN_PY
        self._runtime_metafile = self._runtime_dir + '/readme.text'
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = prcext.ServerProcessStopper(context, 10.0, 'quit')
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        if not await io.file_exists(self._config_file):
            await io.write_file(self._config_file, objconv.obj_to_json(_default_config(), pretty=True))
        await io.create_directory(self._backups_dir, self._log_dir)
        self._context.register(svrext.MaintenanceStateSubscriber(
            self._context, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
        self._context.register(prcext.ServerStateSubscriber(self._context))
        self._context.register(playerstore.PlayersSubscriber(self._context))
        self._context.register(_ServerDetailsSubscriber(self._context))
        self._context.register(_PlayerEventSubscriber(self._context))
        self._context.register(msgext.SyncWrapper(
            self._context, msgext.Archiver(self._context, self._tmp_dir), msgext.SyncReply.AT_START))
        self._context.register(msgext.SyncWrapper(
            self._context, msgext.Unpacker(self._context, self._tmp_dir), msgext.SyncReply.AT_START))
        self._context.register(msglog.LogfileSubscriber(
            self._log_dir + '/%Y%m%d-%H%M%S.log', proch.ServerProcess.FILTER_STDOUT_LINE,
            svrsvc.ServerStatus.RUNNING_FALSE_FILTER, msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._context))
        r.reg('m', interceptors.block_maintenance_only(self._context))
        r.reg('s', interceptors.block_not_started(self._context))
        r.psh('server', svrext.ServerStatusHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(svrsvc.ServerStatus.UPDATED_FILTER))
        r.put('{command}', svrext.ServerCommandHandler(self._context))
        r.pop()
        r.psh('log')
        r.put('tail', httpext.RollingLogHandler(self._context, Server.LOG_FILTER, size=200))
        r.put('subscribe', self._httpsubs.handler(Server.LOG_FILTER, aggtrf.StrJoin('\n')))
        r.pop()
        r.psh('logs', httpext.FileSystemHandler(self._log_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._log_dir, 'path'), 'r')
        r.pop()
        # r.psh('players', _PlayersHandler(self._context))
        r.psh('players', playerstore.PlayersHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(playerstore.EVENT_FILTER, playerstore.EVENT_TRF))
        r.pop()
        r.psh('console')
        r.put('help', httpext.StaticHandler(_COMMANDS_HELP_TEXT))
        r.put('{command}', prcext.ConsoleCommandHandler(self._context, _COMMANDS), 's')
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._config_file), 'm')
        r.pop()
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile))
        r.put('install-runtime', _InstallRuntimeHandler(self), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._context, self._runtime_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._context, self._backups_dir, self._runtime_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._context, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tmp_dir=self._tmp_dir,
            read_tracker=msglog.IntervalTracker(self._context, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._context)), 'm')
        r.pop()
        r.psh(self._httpsubs.resource(resource, 'subscriptions'))
        r.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('Testserver game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._config_file))
        process = proch.ServerProcess(self._context, self._python)
        process.use_pipeinsvc(self._pipeinsvc)
        process.wait_for_started(Server.STARTED_FILTER, 10)
        process.append_arg(self._executable)
        for key in cmdargs.keys():
            process.append_arg(cmdargs[key])
        await process.run()

    async def stop(self):
        await self._stopper.stop()

    async def install_runtime(self, beta: str | None):
        main_py = await pkg.pkg_load('servers.testserver', _MAIN_PY)
        await io.delete_directory(self._runtime_dir)
        await io.create_directory(self._runtime_dir)
        await io.write_file(self._executable, main_py)
        await io.write_file(self._runtime_metafile, 'build : ' + str(dtutil.now_millis()) + '\nbeta  : ' + beta)
        return None


class _InstallRuntimeHandler(httpabc.PostHandler):

    def __init__(self, server: Server):
        self._server = server

    async def handle_post(self, resource, data):
        await self._server.install_runtime(util.get('beta', data, 'none'))
        return httpabc.ResponseBody.NO_CONTENT


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
            result.append({'steamid': str(dtutil.now_millis()), 'name': line[1:]})
        return result


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION, IP, PORT, INGAMETIME = 'versionNumber=', 'public ip:', 'listening on port:', 'Ingametime'
    VERSION_FILTER = msgftr.DataStrContains(VERSION)
    IP_FILTER = msgftr.DataStrContains(IP)
    PORT_FILTER = msgftr.DataStrContains(PORT)
    INGAMETIME_FILTER = msgftr.DataStrContains(INGAMETIME)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.INGAMETIME_FILTER,
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.IP_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.VERSION)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.IP)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': value})
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.PORT)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'port': value})
            return None
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.INGAMETIME)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ingametime': value})
            return None
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT, PLAYER, JOIN, LEAVE = '### Chat', '### Player', 'has joined the server', 'has left the server'
    CHAT_FILTER = msgftr.DataStrContains(CHAT)
    JOIN_FILTER = msgftr.And(msgftr.DataStrContains(PLAYER), msgftr.DataStrContains(JOIN))
    LEAVE_FILTER = msgftr.And(msgftr.DataStrContains(PLAYER), msgftr.DataStrContains(LEAVE))

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.CHAT)
            name = util.right_chop_and_strip(name, ':')
            text = util.left_chop_and_strip(message.data(), ':')
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.PLAYER)
            value = util.right_chop_and_strip(value, _PlayerEventSubscriber.JOIN)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.PLAYER)
            value = util.right_chop_and_strip(value, _PlayerEventSubscriber.LEAVE)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
            return None
        return None
