from __future__ import annotations
import re
# ALLOW core.* palworld.messaging
from core.util import gc, util, idutil, io, objconv
from core.context import contextsvc
from core.http import httprsc, httpext
from core.proc import proch
from core.common import portmapper, rconsvc, svrhelpers

# https://tech.palworldgame.com/settings-and-operation/arguments
APPID = '2394010'


def _default_cmdargs() -> dict:
    return {
        '_comment_port': 'Port number used for player connections. Default is 8211 if not specified.',
        '-port': None,
        '_comment_queryport': 'Port number used for server queries. Default is 27015 if not specified.',
        '-queryport': None,
        '_comment_publicip': 'Manually specify the global IP address of the network on which the server running.',
        '-publicip': None,
        '_comment_publicport': 'Manually specify the port number of the network on which the server running.',
        '-publicport': None,
        '_comment_players': 'Maximum number of participants on the server. Default is 32 if not specified.',
        '-players': None,
        '_comment_useperfthreads': 'Improves performance in multi-threaded CPU environments.',
        '-useperfthreads': False,
        '_comment_NoAsyncLoadingThread': 'Improves performance in multi-threaded CPU environments.',
        '-NoAsyncLoadingThread': False,
        '_comment_UseMultithreadForDS': 'Improves performance in multi-threaded CPU environments.',
        '-UseMultithreadForDS': False,
        '_comment_EpicAppPalServer': 'Setup server as a community server.',
        'EpicApp=PalServer': False,
        '_comment_server_upnp': 'Try to automatically redirect server port on home network using UPnP.',
        'server_upnp': True,
        '_comment_query_upnp': 'Try to automatically redirect query port on home network using UPnP.',
        'query_upnp': True,
        '_comment_rcon_upnp': 'Try to automatically redirect rcon port on home network using UPnP.',
        'rcon_upnp': False
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._save_dir = self._world_dir + '/SaveGames'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._config_dir = self._world_dir + '/Config'
        self._ini_dir = self._config_dir + '/LinuxServer'
        self._settings_file = self._ini_dir + '/PalWorldSettings.ini'

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_ports().init_jobs().init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf',
                         httpext.MtimeHandler().check(self._save_dir).dir(self._ini_dir))
        builder.put_installer_steam(self._runtime_dir, APPID)
        builder.put_wipes(self._runtime_dir, dict(save=self._save_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_config(dict(cmdargs=self._cmdargs_file, settings=self._settings_file))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/PalServer.sh'
        if not await io.file_exists(executable):
            raise FileNotFoundError('PalWorld game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        settings = _SettingsIni(await io.read_file(self._settings_file))
        settings = await self._rcon_config(settings)
        cmdargs = self._map_ports(cmdargs, settings)
        server = proch.ServerProcess(self._context, executable)
        server.use_cwd(self._runtime_dir).append_struct(cmdargs, '=')
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._config_dir, self._ini_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        saved_dir = self._runtime_dir + '/Pal/Saved'
        if not await io.symlink_exists(saved_dir):
            await io.create_symlink(saved_dir, self._world_dir)
        if not await io.file_exists(self._settings_file):
            settings = _SettingsIni(await io.read_file(self._runtime_dir + '/DefaultPalWorldSettings.ini'))
            await io.write_file(self._settings_file, settings.data_no_comments())

    async def _rcon_config(self, settings: _SettingsIni) -> _SettingsIni:
        if settings.get('RCONEnabled') != 'True':
            settings.set('RCONEnabled', 'True')
        rcon_pass = settings.get('AdminPassword')
        if rcon_pass and len(rcon_pass) > 2 and rcon_pass[0] == '"' and rcon_pass[-1] == '"':
            rcon_pass = rcon_pass[1:-1]
        else:
            rcon_pass = idutil.generate_token(10)
            settings.set('AdminPassword', '"' + rcon_pass + '"')
        rcon_port = settings.get('RCONPort')
        if not rcon_port:
            rcon_port = '25575'
            settings.set('RCONPort', rcon_port)
        if settings.dirty():
            await io.write_file(self._settings_file, settings.data())
        rconsvc.RconService.set_config(self._context, self, int(rcon_port), rcon_pass)
        return settings

    def _map_ports(self, cmdargs: dict, settings: _SettingsIni) -> dict:
        upnp_keys = ('server_upnp', 'query_upnp', 'rcon_upnp')
        server_upnp, query_upnp, rcon_upnp = util.unpack_dict(cmdargs, upnp_keys)
        if server_upnp:
            server_port = util.get('-publicport', cmdargs)
            if not server_port:
                server_port = settings.get('PublicPort')
            if not server_port:
                server_port = util.get('-port', cmdargs)
            if not server_port:
                server_port = 8211
            portmapper.map_port(self._context, self, int(server_port), gc.UDP, 'PalWorld UDP server')
        if query_upnp:
            query_port = util.get('-queryport', cmdargs)
            if not query_port:
                query_port = 27015
            portmapper.map_port(self._context, self, int(query_port), gc.UDP, 'PalWorld UDP query')
        if rcon_upnp:
            rcon_port = settings.get('RCONPort')  # This should always be set
            portmapper.map_port(self._context, self, int(rcon_port), gc.TCP, 'PalWorld TCP rcon')
        return util.delete_dict(cmdargs, upnp_keys)


class _SettingsIni:
    KEY_SETTINGS = 'OptionSettings='

    def __init__(self, data: str):
        self._data = data
        self._settings: dict | None = None
        self._dirty = False

    def get(self, key: str) -> str | None:
        self._data_to_settings()
        return util.get(key, self._settings)

    def set(self, key: str, value: str):
        self._data_to_settings()
        self._dirty = True
        self._settings[key] = value

    def dirty(self) -> bool:
        return self._dirty

    def data(self) -> str:
        self._settings_to_data()
        return self._data

    def data_no_comments(self) -> str:
        return '\n'.join([o for o in self.data().split('\n') if o and o[0] != ';'])

    def _data_to_settings(self):
        if self._settings:
            return
        self._settings, settings = {}, None
        for line in self._data.split('\n'):
            if line.startswith(_SettingsIni.KEY_SETTINGS):
                settings = line[16:-1]
        if not settings:
            return
        for element in re.split(''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', settings):
            index = element.find('=')
            if index > -1:
                self._settings[element[0:index]] = element[index + 1:]

    def _settings_to_data(self):
        if not self._dirty or not self._settings:
            return
        data, settings = [], []
        for line in self._data.split('\n'):
            if line.startswith(_SettingsIni.KEY_SETTINGS):
                for key, value in self._settings.items():
                    settings.append(key + '=' + value)
                data.append(_SettingsIni.KEY_SETTINGS + '(' + ','.join(settings) + ')')
            else:
                data.append(line)
        self._dirty, self._data = False, '\n'.join(data)
