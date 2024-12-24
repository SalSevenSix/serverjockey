from collections.abc import Iterable
# ALLOW core.*
from core.util import util, dtutil, objconv, io, cmdutil, aggtrf, pkg
from core.msg import msgabc, msgext, msgftr, msglog, msgtrf
from core.msgc import mc
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs, httpext, httpsec
from core.metrics import mtxinstance
from core.system import svrabc, svrsvc, svrext
from core.proc import proch, prcext
from core.common import interceptors, playerstore, restarts, spstopper

_MAIN_PY = 'main.py'
_COMMANDS = cmdutil.CommandLines(dict(send='{line}'))
_COMMANDS_HELP_TEXT = '''CONSOLE COMMANDS
quit, crash, players,
login {player}, logout {player},
say {player} {text}, kill {player},
broadcast {message}, error {message},
restart-warnings, restart-empty
'''

_LOG_FILTER = mc.ServerProcess.FILTER_ALL_LINES
_ERROR_FILTER = msgftr.And(_LOG_FILTER, msgftr.DataStrStartsWith('### ERROR:'))
_MAINTENANCE_STATE_FILTER = msgftr.Or(msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
_READY_STATE_FILTER = msgftr.Or(msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


def _default_config():
    return {
        'players': 'MrGoober,StabMasterArson,YouMadNow',
        'start_speed_modifier': 1,
        'crash_on_start_seconds': 0.0,
        'ingametime_interval_seconds': 80.0
    }


class Server(svrabc.Server):
    STARTED_FILTER = msgftr.And(
        mc.ServerProcess.FILTER_STDOUT_LINE,
        msgftr.DataStrContains('SERVER STARTED'))

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._python = context.config('python')
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir, self._world_dir = self._home_dir + '/runtime', self._home_dir + '/world'
        self._executable = self._runtime_dir + '/' + _MAIN_PY
        self._runtime_metafile = self._runtime_dir + '/readme.text'
        self._log_dir, self._config_file = self._world_dir + '/logs', self._world_dir + '/config.json'
        self._pipeinsvc = proch.PipeInLineService(context)
        self._stopper = spstopper.ServerProcessStopper(context, 10.0, 'quit')
        self._httpsubs = httpsubs.HttpSubscriptionService(context)

    async def initialise(self):
        await self.build_world()
        await mtxinstance.initialise(self._context, error_filter=_ERROR_FILTER)
        self._context.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE),
            self.build_world))
        self._context.register(svrext.MaintenanceStateSubscriber(
            self._context, _MAINTENANCE_STATE_FILTER, _READY_STATE_FILTER))
        self._context.register(prcext.ServerStateSubscriber(self._context))
        self._context.register(playerstore.PlayersSubscriber(self._context))
        self._context.register(restarts.RestartAfterWarningsSubscriber(
            self._context, _RestartWarningsBuilder(self._context)))
        self._context.register(restarts.RestartOnEmptySubscriber(self._context))
        self._context.register(_ServerDetailsSubscriber(self._context))
        self._context.register(_PlayerEventSubscriber(self._context))
        self._context.register(_AutomaticRestartsSubscriber(self._context))
        self._context.register(msgext.SyncWrapper(
            self._context, msgext.Archiver(self._context, self._tempdir), msgext.SyncReply.AT_START))
        self._context.register(msgext.SyncWrapper(
            self._context, msgext.Unpacker(self._context, self._tempdir), msgext.SyncReply.AT_START))
        self._context.register(msglog.LogfileSubscriber(
            self._log_dir + '/%Y%m%d-%H%M%S.log', mc.ServerProcess.FILTER_STDOUT_LINE,
            mc.ServerStatus.RUNNING_FALSE_FILTER, msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._context))
        r.reg('m', interceptors.block_maintenance_only(self._context))
        r.reg('s', interceptors.block_not_started(self._context))
        r.psh('server', svrext.ServerStatusHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(mc.ServerStatus.UPDATED_FILTER))
        r.put('{command}', svrext.ServerCommandHandler(self._context, restarts.COMMANDS))
        r.pop()
        r.psh('log')
        r.put('tail', httpext.RollingLogHandler(self._context, _LOG_FILTER, size=200))
        r.put('subscribe', self._httpsubs.handler(_LOG_FILTER, aggtrf.StrJoin('\n')))
        r.pop()
        r.psh('logs', httpext.FileSystemHandler(self._log_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._log_dir, 'path'), 'r')
        r.pop()
        r.psh('players', playerstore.PlayersHandler(self._context))
        r.put('subscribe', self._httpsubs.handler(mc.PlayerStore.EVENT_FILTER, mc.PlayerStore.EVENT_TRF))
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
        r.put('world-meta', httpext.MtimeHandler().dir(self._log_dir))
        r.put('wipe-world-all', httpext.WipeHandler(self._context, self._world_dir), 'r')
        r.put('wipe-world-config', httpext.WipeHandler(self._context, self._config_file), 'r')
        r.put('wipe-world-logs', httpext.WipeHandler(self._context, self._log_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._context, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._context, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._context, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tempdir=self._tempdir,
            read_tracker=msglog.IntervalTracker(self._context, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._context)), 'm')
        r.pop()
        r.psh(self._httpsubs.resource(resource, 'subscriptions'))
        r.put('{identity}', self._httpsubs.subscriptions_handler('identity'))

    async def run(self):
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('Testserver game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._config_file))
        server = proch.ServerProcess(self._context, self._python)
        server.use_pipeinsvc(self._pipeinsvc)
        server.wait_for_started(Server.STARTED_FILTER, 10)
        server.append_arg(self._executable)
        for key in cmdargs.keys():
            server.append_arg(cmdargs[key])
        await server.run()

    async def stop(self):
        await self._stopper.stop()

    async def install_runtime(self, beta: str | None):
        await io.delete_directory(self._runtime_dir)
        await io.create_directory(self._runtime_dir)
        main_py = await pkg.pkg_load('servers.testserver', _MAIN_PY)
        await io.write_file(self._executable, main_py)
        await io.write_file(self._runtime_metafile, 'build : ' + str(dtutil.now_millis()) + '\nbeta  : ' + beta)

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._log_dir)
        if not await io.file_exists(self._config_file):
            await io.write_file(self._config_file, objconv.obj_to_json(_default_config(), pretty=True))


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
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        response = await proch.PipeInLineService.request(
            self._context, self, 'players', msgext.MultiCatcher(
                catch_filter=mc.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataStrContains('Players connected'), include_start=False,
                stop_filter=msgftr.DataEquals(''), include_stop=False, timeout=5.0))
        result = []
        if response is None or not isinstance(response, Iterable):
            return result
        for line in [m.data() for m in response]:
            result.append(dict(steamid=str(dtutil.now_millis()), name=line[1:]))
        return result


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION, IP, PORT, INGAMETIME = 'versionNumber=', 'public ip:', 'listening on port:', 'Ingametime'
    VERSION_FILTER = msgftr.DataStrContains(VERSION)
    IP_FILTER = msgftr.DataStrContains(IP)
    PORT_FILTER = msgftr.DataStrContains(PORT)
    INGAMETIME_FILTER = msgftr.DataStrContains(INGAMETIME)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.INGAMETIME_FILTER,
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.IP_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.INGAMETIME)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ingametime=value))
            return None
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=value))
            return None
        if _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.IP)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=value))
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.PORT)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(port=value))
            return None
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    PLAYER, JOIN, LEAVE = '### Player', 'has joined the server', 'has left the server'
    JOIN_FILTER = msgftr.And(msgftr.DataStrContains(PLAYER), msgftr.DataStrContains(JOIN))
    LEAVE_FILTER = msgftr.And(msgftr.DataStrContains(PLAYER), msgftr.DataStrContains(LEAVE))
    CHAT, KILL = '### Chat', '### Kill'
    CHAT_FILTER, KILL_FILTER = msgftr.DataStrContains(CHAT), msgftr.DataStrContains(KILL)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER, _PlayerEventSubscriber.KILL_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER, _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name = util.lchop(message.data(), _PlayerEventSubscriber.CHAT)
            name = util.rchop(name, ':')
            text = util.lchop(message.data(), ':')
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
            return None
        if _PlayerEventSubscriber.KILL_FILTER.accepts(message):
            name = util.lchop(message.data(), _PlayerEventSubscriber.KILL)
            playerstore.PlayersSubscriber.event_death(self._mailer, self, name, 'was killed by admin command')
            return None
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.PLAYER)
            value = util.rchop(value, _PlayerEventSubscriber.JOIN)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.PLAYER)
            value = util.rchop(value, _PlayerEventSubscriber.LEAVE)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
            return None
        return None


class _AutomaticRestartsSubscriber(msgabc.AbcSubscriber):
    AFTER_WARNINGS_RESTART_FILTER = msgftr.DataStrContains('### server restart after warnings')
    ON_EMPTY_RESTART_FILTER = msgftr.DataStrContains('### server restart on empty')

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _AutomaticRestartsSubscriber.AFTER_WARNINGS_RESTART_FILTER,
                _AutomaticRestartsSubscriber.ON_EMPTY_RESTART_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _AutomaticRestartsSubscriber.AFTER_WARNINGS_RESTART_FILTER.accepts(message):
            restarts.RestartAfterWarningsSubscriber.signal_restart(self._mailer, self)
            return None
        if _AutomaticRestartsSubscriber.ON_EMPTY_RESTART_FILTER.accepts(message):
            restarts.RestartOnEmptySubscriber.signal_restart(self._mailer, self)
            return None
        return None


class _RestartWarnings(restarts.RestartWarnings):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer, self._messages = mailer, [
            'broadcast Server restart in 10 seconds.',
            'broadcast Server restart in 30 seconds.']

    async def send_warning(self) -> float:
        if len(self._messages) == 0:
            return 0.0
        await proch.PipeInLineService.request(self._mailer, self, self._messages.pop())
        return 10.0 if len(self._messages) == 0 else 20.0


class _RestartWarningsBuilder(restarts.RestartWarningsBuilder):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def create_warninger(self) -> restarts.RestartWarnings:
        return _RestartWarnings(self._mailer)
