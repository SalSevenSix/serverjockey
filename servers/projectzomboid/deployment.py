# ALLOW core.* projectzomboid.messaging
from core.util import util, io, objconv
from core.msg import msgext, msgftr, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch, jobh
from core.common import steam, interceptors, cachelock
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
        'mod_check_action': 3,
        '_comment_cache_map_files': 'Force map files to be cached in memory while server is running (EXPERIMENTAL)',
        'cache_map_files': False
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._world_name = _WORLD_NAME_DEF
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
        await self.build_world()
        await cachelock.initialise(self._mailer)
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer, self._tempdir), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer, self._tempdir), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf'))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, APPID), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('world-meta', httpext.MtimeHandler().check(self._multiplayer_dir).file(self._log_file))
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-playerdb', httpext.WipeHandler(self._mailer, self._player_dir), 'r')
        r.put('wipe-world-config', httpext.WipeHandler(self._mailer, self._config_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._save_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.put('restore-autobackup', httpext.UnpackerHandler(
            self._mailer, self._autobackups_dir, self._world_dir, to_root=True, wipe=False), 'r')
        r.pop()
        r.put('log', httpext.FileSystemHandler(self._log_file))
        r.psh('logs', httpext.FileSystemHandler(self._logs_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tempdir=self._tempdir,
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')
        r.pop()
        r.psh('autobackups', httpext.FileSystemHandler(self._autobackups_dir, ls_filter=_autobackups))
        r.put('*{path}', httpext.FileSystemHandler(self._autobackups_dir, 'path', ls_filter=_autobackups), 'r')
        r.pop()
        r.psh('config')
        r.put('db', httpext.FileSystemHandler(self._player_dir + '/' + self._world_name + '.db'), 'r')
        r.put('jvm', httpext.FileSystemHandler(self._runtime_dir + '/ProjectZomboid64.json'), 'm')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_file), 'm')
        config_pre = self._config_dir + '/' + self._world_name
        r.put('ini', httpext.FileSystemHandler(config_pre + '.ini'), 'm')
        r.put('sandbox', httpext.FileSystemHandler(config_pre + '_SandboxVars.lua'), 'm')
        r.put('spawnpoints', httpext.FileSystemHandler(config_pre + '_spawnpoints.lua'), 'm')
        r.put('spawnregions', httpext.FileSystemHandler(config_pre + '_spawnregions.lua'), 'm')
        r.put('shop', httpext.FileSystemHandler(self._lua_dir + '/ServerPointsListings.ini'), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/start-server.sh'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Project Zomboid game server not installed. Please Install Runtime first.')
        world_name = await self._get_world_name()
        if world_name != self._world_name:
            raise Exception('Server Name missmatch, ServerJockey needs to be restarted.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('cache_map_files', cmdargs, False):
            cachelock.set_path(self._mailer, self, self._save_dir)
        mck.apply_config(self._mailer, self, cmdargs)
        server = proch.ServerProcess(self._mailer, executable)
        server.append_arg('-cachedir=' + self._world_dir)
        if world_name != _WORLD_NAME_DEF:
            server.append_arg('-servername').append_arg(world_name)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir, self._autobackups_dir,
                                  self._player_dir, self._config_dir, self._save_dir, self._lua_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))

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
