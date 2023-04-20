from core.util import io
from core.msg import msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpstm
from core.proc import proch, jobh
from core.system import interceptors  # TODO should servers call system package?

_WORLD = 'servertest'


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._player_dir = self._world_dir + '/db'
        self._logs_dir = self._world_dir + '/Logs'
        self._config_dir = self._world_dir + '/Server'
        self._save_dir = self._world_dir + '/Saves'
        self._lua_dir = self._world_dir + '/Lua'

    def new_server_process(self):
        return proch.ServerProcess(self._mailer, self._runtime_dir + '/start-server.sh') \
            .append_arg('-cachedir=' + self._world_dir)

    async def initialise(self):
        await self.build_world()
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_380870.acf'))
        r.put('install-runtime', httpstm.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 380870), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-playerdb', httpext.WipeHandler(self._mailer, self._player_dir), 'r')
        r.put('wipe-world-config', httpext.WipeHandler(self._mailer, self._config_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._save_dir), 'r')
        r.put('wipe-world-backups', httpext.WipeHandler(self._mailer, self._world_dir + '/backups'), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.put('log', httpext.FileSystemHandler(self._world_dir + '/server-console.txt'))
        r.psh('logs', httpext.FileSystemHandler(self._logs_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'))
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'), 'm')
        r.pop()
        r.psh('config')
        r.put('db', httpext.FileSystemHandler(self._player_dir + '/' + _WORLD + '.db'), 'r')
        r.put('jvm', httpext.FileSystemHandler(self._runtime_dir + '/ProjectZomboid64.json'))
        config_pre = self._config_dir + '/' + _WORLD
        r.put('ini', httpext.FileSystemHandler(config_pre + '.ini'))
        r.put('sandbox', httpext.FileSystemHandler(config_pre + '_SandboxVars.lua'))
        r.put('spawnpoints', httpext.FileSystemHandler(config_pre + '_spawnpoints.lua'))
        r.put('spawnregions', httpext.FileSystemHandler(config_pre + '_spawnregions.lua'))
        r.put('shop', httpext.FileSystemHandler(self._lua_dir + '/ServerPointsListings.ini'))

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._player_dir)
        await io.create_directory(self._config_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._lua_dir)
