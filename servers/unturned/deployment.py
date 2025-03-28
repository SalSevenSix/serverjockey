# ALLOW core.* unturned.messaging
from core.util import gc, util, io, objconv, linenc
from core.context import contextsvc
from core.http import httprsc, httpext
from core.proc import proch, wrapper
from core.common import portmapper, svrhelpers
from servers.unturned import messaging as msg

APPID = '1110390'


def _default_cmdargs():
    return {
        '_comment_scope': 'Server scope. Options are InternetServer or LanServer',
        'scope': 'InternetServer',
        '_comment_upnp': 'Try to automatically redirect ports on home network using UPnP',
        'upnp': True
    }


# https://github.com/SmartlyDressedGames/U3-Docs/blob/master/ServerHosting.md#How-to-Launch-Server-on-Linux
# https://unturned.info/Server-Hosting/ServerHosting/
class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._python, self._wrapper = context.config('python'), None
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._save_dir = self._world_dir + '/save'
        self._savesvr_dir = self._save_dir + '/Server'
        self._map_dir = self._save_dir + '/Level'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._settings_file = self._save_dir + '/Config.json'
        self._workshop_file = self._save_dir + '/WorkshopDownloadConfig.json'
        self._commands_file = self._savesvr_dir + '/Commands.dat'
        self._env = context.env()
        self._env['TERM'] = 'xterm'
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir + '/linux64'

    async def initialise(self):
        self._wrapper = await wrapper.write_wrapper(self._home_dir)
        await self.build_world()
        helper = svrhelpers.DeploymentInitHelper(self._context, self.build_world)
        helper.init_ports().init_jobs().init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf',
                         httpext.MtimeHandler().check(self._map_dir).dir(self._logs_dir))
        builder.put_installer_steam(self._runtime_dir, APPID)
        builder.put_wipes(self._runtime_dir, dict(save=self._map_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_config(dict(
            cmdargs=self._cmdargs_file, commands=self._commands_file,
            settings=self._settings_file, workshop=self._workshop_file))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/Unturned_Headless.x86_64'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Unturned game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('upnp', cmdargs, True):
            await self._map_ports()
        server = proch.ServerProcess(self._context, self._python)
        server.use_env(self._env).use_out_decoder(linenc.PtyLineDecoder())
        server.append_arg(self._wrapper).append_arg(executable)
        server.append_arg('-batchmode').append_arg('-nographics')
        server.append_arg('+' + util.get('scope', cmdargs, 'InternetServer') + '/Save')
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir, self._save_dir, self._savesvr_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        logs_dir = self._runtime_dir + '/Logs'
        if not await io.symlink_exists(logs_dir):
            await io.create_symlink(logs_dir, self._logs_dir)
        servers_dir = self._runtime_dir + '/Servers'
        await io.create_directory(servers_dir)
        save_dir = servers_dir + '/Save'
        if not await io.symlink_exists(save_dir):
            await io.create_symlink(save_dir, self._save_dir)

    async def _map_ports(self):
        port_key, port = 'port', msg.DEFAULT_PORT
        if await io.file_exists(self._commands_file):
            commands = await io.read_file(self._commands_file)
            for line in commands.split('\n'):
                if line and line.lower().startswith(port_key):
                    port = int(util.lchop(line.lower(), port_key))
        portmapper.map_port(self._context, self, port, gc.UDP, 'Unturned query')
        portmapper.map_port(self._context, self, port + 1, gc.UDP, 'Unturned server')
