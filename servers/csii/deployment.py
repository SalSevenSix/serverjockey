import sys
# ALLOW core.* csii.messaging
from core.util import gc, util, idutil, io, objconv, steamutil
from core.context import contextsvc
from core.http import httprsc, httpext
from core.proc import proch, wrapper
from core.common import portmapper, rconsvc, svrhelpers
from servers.csii import messaging as msg

APPID = '730'


def _default_cmdargs() -> dict:
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
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._config_dir = self._world_dir + '/cfg'
        self._config_files = _init_config_files(self._runtime_dir + '/game/csgo/cfg', self._config_dir)
        self._wrapper = None

    async def initialise(self):
        self._wrapper = await wrapper.write_wrapper(self._home_dir)
        await steamutil.link_steamclient_to_sdk(self._context.env('HOME'))
        await self.build_world()
        helper = svrhelpers.DeploymentInitHelper(self._context, self.build_world)
        helper.init_ports().init_jobs().init_archiving(self._tempdir)
        helper.init_logging(self._logs_dir, msg.CONSOLE_LOG_FILTER).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/VERSIONS.txt', httpext.MtimeHandler().dir(self._logs_dir))
        builder.put_installer_steam(self._runtime_dir, APPID, anon=False)
        builder.put_wipes(self._runtime_dir, dict(all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_steamcmd()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        configs = dict(cmdargs=self._cmdargs_file)
        for config_file in self._config_files:
            configs[config_file.identity()] = config_file.world_path()
        builder.put_config(configs)

    async def new_server_process(self) -> proch.ServerProcess:
        bin_dir = self._runtime_dir + '/game/bin/linuxsteamrt64'
        executable = bin_dir + '/cs2'
        if not await io.file_exists(executable):
            raise FileNotFoundError('CS2 game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        server_port = util.get('-port', cmdargs, 27015)
        if util.get('upnp', cmdargs, True):
            portmapper.map_port(self._context, self, server_port, gc.TCP, 'CS2 TCP server')
            portmapper.map_port(self._context, self, server_port, gc.UDP, 'CS2 UDP server')
        rconsvc.RconService.set_config(self._context, self, server_port, util.get('+rcon_password', cmdargs))
        server = proch.ServerProcess(self._context, sys.executable).use_cwd(bin_dir)
        server.append_arg(self._wrapper).append_arg(executable).append_arg('-dedicated')
        server.append_struct(util.delete_dict(cmdargs, ('upnp', '-dedicated')))
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
