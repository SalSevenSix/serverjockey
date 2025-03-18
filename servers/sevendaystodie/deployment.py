from xml.dom import minidom
# ALLOW core.* sevendaystodie.messaging
from core.util import gc, util, objconv, io, pack, idutil
from core.msgc import sc
from core.context import contextsvc
from core.http import httprsc, httpext
from core.system import svrsvc
from core.proc import proch
from core.common import portmapper, svrhelpers
from servers.sevendaystodie import messaging as msg

APPID = '294420'


def _default_cmdargs():
    return {
        '_comment_server_upnp': 'Try to automatically redirect server ports on home network using UPnP',
        'server_upnp': True,
        '_comment_console_upnp': 'Try to automatically redirect web console port on home network using UPnP',
        'console_upnp': False,
        '_comment_telnet_upnp': 'Try to automatically redirect telnet port on home network using UPnP',
        'telnet_upnp': False
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._settings_def_file = self._runtime_dir + '/serverconfig.xml'
        self._executable = self._runtime_dir + '/7DaysToDieServer.x86_64'
        self._mods_live_dir = self._runtime_dir + '/Mods'
        self._world_dir = self._home_dir + '/world'
        self._config_dir = self._world_dir + '/config'
        self._save_dir = self._world_dir + '/save'
        self._logs_dir = self._world_dir + '/logs'
        self._mods_src_dir = self._world_dir + '/mods'
        self._cmdargs_file = self._config_dir + '/cmdargs.json'
        self._settings_file = self._config_dir + '/serverconfig.xml'
        self._live_file = self._config_dir + '/serverconfig-live.xml'
        self._admin_file = self._config_dir + '/serveradmin.xml'
        self._env = context.env()
        self._env['LD_LIBRARY_PATH'] = '.'

    async def initialise(self):
        await self.build_world()
        helper = svrhelpers.DeploymentInitHelper(self._context, self.build_world)
        helper.init_ports().init_jobs().init_archiving(self._tempdir)
        helper.init_logging(self._logs_dir, msg.CONSOLE_LOG_FILTER).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf',
                         httpext.MtimeHandler().check(self._save_dir + '/Saves').dir(self._logs_dir))
        builder.put_installer_steam(self._runtime_dir, APPID)
        builder.put_wipes(self._runtime_dir, dict(save=self._save_dir, config=self._config_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_config(dict(cmdargs=self._cmdargs_file, settings=self._settings_file, admin=self._admin_file))
        builder.psh('modfiles', httpext.FileSystemHandler(self._mods_src_dir, ls_filter=_is_modfile))
        builder.put('*{path}', httpext.FileSystemHandler(self._mods_src_dir, 'path', tempdir=self._tempdir), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('7D2D game server not installed. Please Install Runtime first.')
        svrsvc.ServerStatus.notify_state(self._context, self, sc.START)  # pushing early because slow pre-start tasks
        config = await self._build_live_config()
        await self._sync_mods()
        await self._map_ports(config)
        server = proch.ServerProcess(self._context, self._executable)
        server.use_env(self._env).use_cwd(self._runtime_dir)
        server.append_arg('-quit').append_arg('-batchmode').append_arg('-nographics')
        server.append_arg('-dedicated').append_arg('-configfile=' + self._live_file)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._config_dir,
                                  self._save_dir, self._logs_dir, self._mods_src_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        await io.create_directory(self._mods_live_dir)
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        if not await io.file_exists(self._settings_file):
            await io.copy_text_file(self._settings_def_file, self._settings_file)

    async def _build_live_config(self) -> dict:
        live_dict = {}
        subs = {
            'AdminFileName': '../../config/serveradmin.xml',
            'UserDataFolder': self._save_dir,
            'SaveGameFolder': None
        }
        xml = await io.read_file(self._settings_file)
        original = minidom.parseString(xml).firstChild
        # noinspection PyUnresolvedReferences
        live = minidom.Element(original.tagName)
        doc = minidom.Document()
        doc.appendChild(live)
        live.ownerDocument = doc
        for node in original.childNodes:
            if isinstance(node, minidom.Element):
                name = node.getAttribute('name')
                if name in subs:
                    if subs[name] is not None:
                        live_node = minidom.Element(node.tagName)
                        live_node.ownerDocument = doc
                        live_node.setAttribute('name', name)
                        live_node.setAttribute('value', subs[name])
                        live.appendChild(live_node)
                        live_dict[name] = subs[name]
                    del subs[name]
                else:
                    live.appendChild(node)
                    live_dict[name] = node.getAttribute('value')
        for name, value in subs.items():
            if value is not None:
                live_node = minidom.Element('property')
                live_node.ownerDocument = doc
                live_node.setAttribute('name', name)
                live_node.setAttribute('value', value)
                live.appendChild(live_node)
                live_dict[name] = value
        await io.write_file(self._live_file, doc.toxml())
        return live_dict

    async def _map_ports(self, config: dict):
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('server_upnp', cmdargs, True):
            server_port = int(util.get('ServerPort', config, 26900))
            portmapper.map_port(self._context, self, server_port, gc.TCP, '7D2D TCP server')
            portmapper.map_port(self._context, self, server_port, gc.UDP, '7D2D UDP server')
            portmapper.map_port(self._context, self, server_port + 1, gc.UDP, '7D2D aux1')
            portmapper.map_port(self._context, self, server_port + 2, gc.UDP, '7D2D aux2')
            portmapper.map_port(self._context, self, server_port + 3, gc.UDP, '7D2D aux3')
        if util.get('console_upnp', cmdargs, False) and objconv.to_bool(util.get('WebDashboardEnabled', config)):
            console_port = int(util.get('WebDashboardPort', config, 8080))
            portmapper.map_port(self._context, self, console_port, gc.TCP, '7D2D web console')
        if util.get('telnet_upnp', cmdargs, False) and objconv.to_bool(util.get('TelnetEnabled', config)):
            telnet_port = int(util.get('TelnetPort', config, 8081))
            portmapper.map_port(self._context, self, telnet_port, gc.TCP, '7D2D telnet')

    async def _sync_mods(self):
        self._context.post(self, msg.DEPLOYMENT_MSG, 'MOD syncing...')
        tracking_file, data, modfiles = self._mods_src_dir + '/mods.json', {}, []
        if await io.file_exists(tracking_file):
            data = objconv.json_to_dict(await io.read_file(tracking_file))
            data = data if data else {}
        for file in [o for o in await io.directory_list(self._mods_src_dir) if _is_modfile(o)]:
            name, file_mtime = file['name'], file['mtime']
            entry = util.get(name, data, dict(mtime=None, livedir=None, synced=False))
            entry_mtime, livedir, synced = entry['mtime'], entry['livedir'], entry['synced']
            synced = synced and livedir and entry_mtime and entry_mtime == file_mtime
            synced = synced and await io.directory_exists(self._mods_live_dir + '/' + livedir)
            data[name] = dict(mtime=file_mtime, livedir=livedir, synced=synced)
            modfiles.append(name)
        for name in data.keys():
            if name not in modfiles:
                data[name]['synced'] = False
        await io.write_file(tracking_file, objconv.obj_to_json(data, True))
        for name, entry in data.copy().items():
            mtime, livedir, synced = entry['mtime'], entry['livedir'], entry['synced']
            if not synced:
                livedir = await self._sync_mod(name, livedir)
                if livedir:
                    data[name] = dict(mtime=mtime, livedir=livedir, synced=True)
                else:
                    del data[name]
                await io.write_file(tracking_file, objconv.obj_to_json(data))
        await io.write_file(tracking_file, objconv.obj_to_json(data, True))

    async def _sync_mod(self, name: str, livedir: str) -> str | None:
        working_dir, modinfo, modfile = None, 'ModInfo.xml', self._mods_src_dir + '/' + name
        try:
            if livedir:
                await io.delete_any(self._mods_live_dir + '/' + livedir)
            if not await io.file_exists(modfile):
                self._context.post(self, msg.DEPLOYMENT_MSG, 'MOD ' + name + ' not found, removed from server.')
                return None
            working_dir = self._tempdir + '/' + idutil.generate_id()
            await io.create_directory(working_dir)
            await pack.unpack_archive(modfile, working_dir)
            source = await io.find_files(working_dir, modinfo)
            if len(source) == 0:
                self._context.post(self, msg.DEPLOYMENT_MSG, 'MOD ' + name + ' has no ' + modinfo)
                return None
            source = source[0][0:-1 - len(modinfo)]
            livedir = name[0:-1 - len(util.fext(name))] if source == working_dir else util.fname(source)
            target = self._mods_live_dir + '/' + livedir
            await io.delete_any(target)
            await io.move_path(source, target)
            self._context.post(self, msg.DEPLOYMENT_MSG, 'MOD ' + name + ' installed successfully.')
            return livedir
        finally:
            await io.delete_directory(working_dir)


def _is_modfile(entry) -> bool:
    ftype, fname, fext = entry['type'], entry['name'], util.fext(entry['name'])
    return ftype == 'file' and fname != fext and fext == 'zip'
