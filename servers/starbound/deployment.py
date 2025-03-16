# ALLOW core.* starbound.messaging
from core.util import gc, util, idutil, io, objconv
from core.context import contextsvc
from core.http import httpabc, httpext
from core.proc import proch
from core.common import rconsvc, portmapper, svrhelpers
from servers.starbound import messaging as msg

# STARBOUND https://starbounder.org/Guide:LinuxServerSetup
APPID = '211820'


def _default_cmdargs():
    return {
        '_comment_server_upnp': 'Try to automatically redirect server ports on home network using UPnP',
        'server_upnp': True,
        '_comment_rcon_upnp': 'Try to automatically redirect rcon port on home network using UPnP',
        'rcon_upnp': False
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._save_dir = self._world_dir + '/universe'
        self._log_file = self._world_dir + '/starbound_server.log'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._config_file = self._world_dir + '/starbound_server.config'

    async def initialise(self):
        await self.build_world()
        helper = svrhelpers.DeploymentInitHelper(self._context, self.build_world)
        helper.init_ports().init_jobs().init_archiving(self._tempdir).done()

    def resources(self, resource: httpabc.Resource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf',
                         httpext.MtimeHandler().check(self._save_dir).file(self._log_file))
        builder.put_installer_steam(self._runtime_dir, APPID, anon=False)
        builder.put_wipes(self._runtime_dir, dict(save=self._save_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_steamcmd()
        builder.put_log(self._log_file).put_logs(self._world_dir, ls_filter=_logfiles)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_config(dict(cmdargs=self._cmdargs_file, settings=self._config_file))

    async def new_server_process(self) -> proch.ServerProcess:
        config, bin_dir = {}, self._runtime_dir + '/linux'
        executable = bin_dir + '/starbound_server'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Starbound game server not installed. Please Install Runtime first.')
        if await io.file_exists(self._config_file):
            config = objconv.json_to_dict(await io.read_file(self._config_file))
            config = await self._rcon_config(config)
        await self._map_ports(config)
        await self._link_mods()
        return proch.ServerProcess(self._context, executable).use_cwd(bin_dir)

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        storage_dir = self._runtime_dir + '/storage'
        if not await io.symlink_exists(storage_dir):
            await io.create_symlink(storage_dir, self._world_dir)

    async def _rcon_config(self, config: dict) -> dict:
        port, password = util.get('rconServerPort', config), util.get('rconServerPassword', config)
        port = port if port else 21026
        password = password if password else idutil.generate_token(10)
        rconsvc.RconService.set_config(self._context, self, port, password)
        config['runRconServer'], config['rconServerPort'], config['rconServerPassword'] = True, port, password
        await io.write_file(self._config_file, objconv.obj_to_json(config, pretty=True))
        return config

    async def _map_ports(self, config: dict):
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('server_upnp', cmdargs, True):
            server_port = util.get('gameServerPort', config, 21025)
            query_port = util.get('queryServerPort', config, server_port)
            portmapper.map_port(self._context, self, server_port, gc.TCP, 'Starbound server')
            if query_port != server_port:
                portmapper.map_port(self._context, self, query_port, gc.TCP, 'Starbound query')
        if util.get('rcon_upnp', cmdargs, False):
            rcon_port = util.get('rconServerPort', config)
            portmapper.map_port(self._context, self, rcon_port, gc.TCP, 'Starbound rcon')

    async def _link_mods(self):
        self._context.post(self, msg.DEPLOYMENT_MSG, 'INFO  Including subscribed workshop mods...')
        workshop_files, workshop_dir = [], self._runtime_dir + '/steamapps/workshop/content/' + APPID
        if await io.directory_exists(workshop_dir):
            workshop_files = await io.directory_list(workshop_dir)
        workshop_items, mods_dir = ['mods_go_here'], self._runtime_dir + '/mods'
        for workshop_item in [str(o['name']) for o in workshop_files if o['type'] == 'directory']:
            pack_file = workshop_dir + '/' + workshop_item + '/contents.pak'
            if await io.file_exists(pack_file):
                self._context.post(self, msg.DEPLOYMENT_MSG, 'INFO  Adding   ' + workshop_item)
                workshop_items.append(workshop_item + '.pak')
                link_file = mods_dir + '/' + workshop_item + '.pak'
                if not await io.symlink_exists(link_file):
                    await io.create_symlink(link_file, pack_file)
            else:
                self._context.post(self, msg.DEPLOYMENT_MSG,
                                   'ERROR Adding   ' + workshop_item + ' because contents.pak not found')
        for mod_file in [o['name'] for o in await io.directory_list(mods_dir) if o['name'] not in workshop_items]:
            self._context.post(self, msg.DEPLOYMENT_MSG, 'INFO  Removing ' + mod_file[:-4])
            await io.delete_file(mods_dir + '/' + mod_file)


def _logfiles(entry) -> bool:
    return entry['type'] == 'file' and entry['name'].startswith('starbound_server.log')
