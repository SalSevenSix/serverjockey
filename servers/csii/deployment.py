# ALLOW core.* csii.messaging
from core.util import gc, util, idutil, io, objconv, steamutil
from core.msg import msgext, msgftr, msglog, msgtrf
from core.msgc import mc
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch, jobh, wrapper
from core.common import steam, interceptors, portmapper, rconsvc
from servers.csii import messaging as msg


def _default_cmdargs():
    return {
        '_comment_ip': 'IP binding.',
        '-ip': '0.0.0.0',
        '_comment_port': 'Port for server to open and use.',
        '-port': 27015,
        '_comment_rcon_password': 'Password to use for rcon, also enables rcon.',
        '+rcon_password': idutil.generate_token(10),
        '_comment_game_type': 'Game type.',
        '+game_type': 0,
        '_comment_game_mode': 'Game mode.',
        '+game_mode': 1,
        '_comment_map': 'Initial map to use.',
        '+map': 'de_dust2',
        '_comment_upnp': 'Try to automatically redirect server port on home network using UPnP.',
        'upnp': True
    }


def _init_config_files(runtime_path: str, world_path: str) -> tuple:
    return (
        _ConfigFile('server', 'server.cfg', runtime_path, world_path),
        _ConfigFile('gamemode-competitive', 'gamemode_competitive.cfg', runtime_path, world_path),
        _ConfigFile('gamemode-wingman', 'gamemode_competitive2v2.cfg', runtime_path, world_path),
        _ConfigFile('gamemode-casual', 'gamemode_casual.cfg', runtime_path, world_path),
        _ConfigFile('gamemode-deathmatch', 'gamemode_deathmatch.cfg', runtime_path, world_path),
        _ConfigFile('gamemode-custom', 'gamemode_custom.cfg', runtime_path, world_path)
    )


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._user_home_dir = context.env('HOME')
        self._python, self._wrapper = context.config('python'), None
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._config_dir = self._world_dir + '/cfg'
        self._config_files = _init_config_files(self._runtime_dir + '/game/csgo/cfg', self._config_dir)

    async def initialise(self):
        self._wrapper = await wrapper.write_wrapper(self._home_dir)
        await steamutil.link_steamclient_to_sdk(self._user_home_dir)
        await self.build_world()
        self._mailer.register(portmapper.PortMapperService(self._mailer))
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer, self._tempdir), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer, self._tempdir), msgext.SyncReply.AT_START))
        roll_filter = msgftr.Or(mc.ServerStatus.RUNNING_FALSE_FILTER, msgftr.And(
            httpext.WipeHandler.FILTER_DONE, msgftr.DataStrStartsWith(self._logs_dir, invert=True)))
        self._mailer.register(msglog.LogfileSubscriber(
            self._logs_dir + '/%Y%m%d-%H%M%S.log', msg.CONSOLE_LOG_FILTER, roll_filter, msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/VERSIONS.txt'))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 730, anon=False), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('world-meta', httpext.MtimeHandler().dir(self._logs_dir))
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('steamcmd')
        r.put('login', steam.SteamCmdLoginHandler(self._mailer))
        r.put('input', steam.SteamCmdInputHandler(self._mailer))
        r.pop()
        r.psh('logs', httpext.FileSystemHandler(self._logs_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tempdir=self._tempdir,
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_file), 'm')
        for config_file in self._config_files:
            r.put(config_file.identity(), httpext.FileSystemHandler(config_file.world_path()), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        bin_dir = self._runtime_dir + '/game/bin/linuxsteamrt64'
        executable = bin_dir + '/cs2'
        if not await io.file_exists(executable):
            raise FileNotFoundError('CS2 game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        server_port = util.get('-port', cmdargs, 27015)
        if util.get('upnp', cmdargs, True):
            portmapper.map_port(self._mailer, self, server_port, gc.TCP, 'CS2 TCP server')
            portmapper.map_port(self._mailer, self, server_port, gc.UDP, 'CS2 UDP server')
        rconsvc.RconService.set_config(self._mailer, self, server_port, util.get('+rcon_password', cmdargs))
        server = proch.ServerProcess(self._mailer, self._python).use_cwd(bin_dir)
        server.append_arg(self._wrapper).append_arg(executable).append_arg('-dedicated')
        for key, value in cmdargs.items():
            if key != 'upnp' and key != '-dedicated' and not key.startswith('_'):
                if value and isinstance(value, bool):
                    server.append_arg(key)
                else:
                    server.append_arg(key).append_arg(value)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir, self._config_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        for config_file in self._config_files:
            await config_file.build_link()


class _ConfigFile:

    def __init__(self, identity: str, name: str, runtime_path: str, world_path: str):
        self._identity, self._name = identity, name
        self._runtime_path = runtime_path + '/' + name
        self._world_path = world_path + '/' + name

    def identity(self):
        return self._identity

    def name(self):
        return self._name

    def world_path(self):
        return self._world_path

    async def build_link(self):
        if not await io.symlink_exists(self._runtime_path):
            if not await io.file_exists(self._world_path):
                if await io.file_exists(self._runtime_path):
                    await io.copy_text_file(self._runtime_path, self._world_path)
                else:
                    await io.write_file(self._world_path, '')
            await io.create_symlink(self._runtime_path, self._world_path)
