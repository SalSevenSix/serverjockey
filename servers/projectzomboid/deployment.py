import sys
# ALLOW core.* projectzomboid.messaging projectzomboid.modcheck projectzomboid.scrapers
from core.util import util, io, objconv, shellutil, idutil
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch
from core.common import svrhelpers, cachelock
from servers.projectzomboid import messaging as msg, modcheck as mck, scrapers as skr

APPID = '380870'
_WORLD_NAME_DEF = 'servertest'
_EXT_LUAFILES = 'txt', 'text', 'log', 'json', 'ini', 'lua'


def _default_cmdargs() -> dict:
    return {
        '_comment_mod_check_minutes': 'Check interval for updated mods in minutes. Use 0 to disable checks.',
        'mod_check_minutes': 30,
        '_comment_mod_check_action':
            'Action to take after updated mods have been detected. '
            'Options: 1=NotifyOnly 2=RestartOnEmpty 3=RestartAfterWarnings 4=RestartImmediately',
        'mod_check_action': 3,
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
        self._context.register(skr.ScraperService(self._context, self._logs_dir))
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
        builder.put_restore_autobackup(httpext.UnpackerHandler(
            self._context, self._autobackups_dir, self._world_dir, to_root=True, wipe=False))
        builder.pop()
        builder.put_log(self._log_file).put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_autobackups(self._autobackups_dir, ls_filter=_ls_autobackups, ls_ffilter=_ls_autobackups)
        builder.psh('luafiles', httpext.FileSystemHandler(self._lua_dir, ls_filter=_ls_luafiles))
        builder.put('*{path}', httpext.FileSystemHandler(self._lua_dir, 'path', ls_filter=_ls_luafiles), 'm')
        builder.pop()
        config_pre = self._config_dir + '/' + self._world_name
        player_db = self._player_dir + '/' + self._world_name + '.db'
        builder.put('playerdb', _PlayerDbHandler(self._context, player_db), 'm')
        builder.put_config(dict(
            jvm=self._runtime_dir + '/ProjectZomboid64.json', cmdargs=self._cmdargs_file,
            ini=config_pre + '.ini', sandbox=config_pre + '_SandboxVars.lua',
            spawnpoints=config_pre + '_spawnpoints.lua', spawnregions=config_pre + '_spawnregions.lua',
            db=player_db, shop=self._lua_dir + '/ServerPointsListings.ini'))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/start-server.sh'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Project Zomboid game server not installed. Please Install Runtime first.')
        world_name = await self._get_world_name()
        if world_name != self._world_name:
            raise Exception('Server Name missmatch, ServerJockey needs to be restarted.')
        await self._prestart_ini()
        await self._prestart_cmdargs()
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

    async def _prestart_cmdargs(self):
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('cache_map_files', cmdargs, False):
            cachelock.set_path(self._context, self, self._save_dir)
        mck.apply_config(self._context, self, cmdargs)

    async def _prestart_ini(self):
        ini_file = self._config_dir + '/' + self._world_name + '.ini'
        if not await io.file_exists(ini_file):
            return
        ini_read = await io.read_file(ini_file)
        ini_read = ini_read.split('\n')
        for line_read in ini_read:
            if line_read and line_read.find('=') > 0:
                if line_read.startswith('DefaultPort='):
                    self._context.post(self, msg.SERVER_PORT, util.lchop(line_read, '='))

    async def _get_world_name(self) -> str:
        if await io.directory_exists(self._multiplayer_dir):
            for entry in await io.directory_list(self._multiplayer_dir):
                if entry['type'] == 'directory':
                    return entry['name']
        return _WORLD_NAME_DEF


class _PlayerDbHandler(httpabc.GetHandler, httpabc.PostHandler):

    def __init__(self, context: contextsvc.Context, player_db: str):
        self._context, self._player_db = context, player_db
        self._executable = None

    async def _get_executable(self) -> str:
        if self._executable:
            return self._executable
        self._executable = await io.find_in_env_path(self._context.env('PATH'), 'sqlite3')
        if not self._executable:
            self._executable = sys.executable + ' -m sqlite3'
        return self._executable

    async def handle_get(self, resource, data):
        dbexists = await io.file_exists(self._player_db)
        executable = await self._get_executable()
        return dict(dbexists=dbexists, executable=executable)

    async def handle_post(self, resource, data):
        sql = util.get('body', data)
        if not sql:
            return '! No SQL provided'
        if not await io.file_exists(self._player_db):
            return '! Player DB not found, server must be run once to create it'
        rid = idutil.generate_id()
        script = await self._get_executable()
        script += ' ' + self._player_db + ' <<\'' + rid + '\'\n' + sql.strip() + '\n' + rid
        result = await shellutil.run_script_text(script)
        return result if result else '! No results'


def _ls_autobackups(entry) -> bool:
    ftype, fname = entry['type'], entry['name']
    return ftype == 'directory' or (ftype == 'file' and fname.startswith('backup_') and fname.endswith('.zip'))


def _ls_luafiles(entry) -> bool:
    ftype, fext = entry['type'], util.fext(entry['name'])
    return ftype == 'directory' or (ftype == 'file' and fext in _EXT_LUAFILES)
