# ALLOW core.* projectzomboid.messaging
from core.util import util, io, objconv
from core.context import contextsvc
from core.http import httprsc, httpext
from core.proc import proch
from core.common import svrhelpers, cachelock
from servers.projectzomboid import modcheck as mck

APPID = '380870'
_WORLD_NAME_DEF = 'servertest'


def _default_cmdargs() -> dict:
    return {
        '_comment_mod_check_minutes': 'Check interval for updated mods in minutes. Use 0 to disable checks.',
        'mod_check_minutes': 20,
        '_comment_mod_check_action':
            'Action to take after updated mods have been detected. '
            'Options: 1=NotifyOnly 2=RestartOnEmpty 3=RestartAfterWarnings 4=RestartImmediately',
        'mod_check_action': 2,
        '_comment_cache_map_files': 'Force map files to be cached in memory while server is running.',
        'cache_map_files': False
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context, self._world_name = context, _WORLD_NAME_DEF
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._autobackups_dir = self._world_dir + '/backups'
        self._player_dir = self._world_dir + '/db'
        self._log_file = self._world_dir + '/server-console.txt'
        self._logs_dir = self._world_dir + '/Logs'
        self._lua_dir = self._world_dir + '/Lua'
        self._config_dir = self._world_dir + '/Server'
        self._cmdargs_file = self._config_dir + '/cmdargs.json'
        self._save_dir = self._world_dir + '/Saves'
        self._multiplayer_dir = self._save_dir + '/Multiplayer'

    async def initialise(self):
        self._world_name = await self._get_world_name()
        await cachelock.initialise(self._context)
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_jobs().init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf',
                         httpext.MtimeHandler().check(self._multiplayer_dir).file(self._log_file))
        builder.put_installer_steam(self._runtime_dir, APPID)
        builder.put_wipes(self._runtime_dir, dict(
            save=self._save_dir, playerdb=self._player_dir, logs=self._logs_dir, lua=self._lua_dir,
            config=self._config_dir, autobackups=self._autobackups_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.put('restore-autobackup', httpext.UnpackerHandler(
                    self._context, self._autobackups_dir, self._world_dir, to_root=True, wipe=False), 'r')
        builder.pop()
        builder.put_log(self._log_file).put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.psh('autobackups', httpext.FileSystemHandler(self._autobackups_dir, ls_filter=_autobackups))
        builder.put('*{path}', httpext.FileSystemHandler(self._autobackups_dir, 'path', ls_filter=_autobackups), 'r')
        builder.pop()
        config_pre = self._config_dir + '/' + self._world_name
        builder.put_config(dict(
            db=self._player_dir + '/' + self._world_name + '.db', jvm=self._runtime_dir + '/ProjectZomboid64.json',
            cmdargs=self._cmdargs_file, ini=config_pre + '.ini', sandbox=config_pre + '_SandboxVars.lua',
            spawnpoints=config_pre + '_spawnpoints.lua', spawnregions=config_pre + '_spawnregions.lua',
            shop=self._lua_dir + '/ServerPointsListings.ini'))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/start-server.sh'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Project Zomboid game server not installed. Please Install Runtime first.')
        world_name = await self._get_world_name()
        if world_name != self._world_name:
            raise Exception('Server Name missmatch, ServerJockey needs to be restarted.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('cache_map_files', cmdargs, False):
            cachelock.set_path(self._context, self, self._save_dir)
        mck.apply_config(self._context, self, cmdargs)
        server = proch.ServerProcess(self._context, executable)
        server.append_arg('-cachedir=' + self._world_dir)
        if world_name != _WORLD_NAME_DEF:
            server.append_arg('-servername').append_arg(world_name)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir, self._autobackups_dir,
                                  self._player_dir, self._config_dir, self._save_dir, self._lua_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        await io.keyfill_json_file(self._cmdargs_file, _default_cmdargs())

    async def _get_world_name(self) -> str:
        if await io.directory_exists(self._multiplayer_dir):
            for entry in await io.directory_list(self._multiplayer_dir):
                if entry['type'] == 'directory':
                    return entry['name']
        return _WORLD_NAME_DEF


def _autobackups(entry) -> bool:
    if entry['type'] == 'directory':
        return True
    return entry['name'].startswith('backup_') and entry['name'].endswith('.zip')
