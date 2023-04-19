from core.util import io
from core.msg import msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpstm
from core.proc import proch, jobh

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
        r.push('deployment')
        r.append('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_380870.acf'))
        r.append('install-runtime', httpstm.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 380870))
        r.append('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir))
        r.append('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir))
        r.append('wipe-world-playerdb', httpext.WipeHandler(self._mailer, self._player_dir))
        r.append('wipe-world-config', httpext.WipeHandler(self._mailer, self._config_dir))
        r.append('wipe-world-save', httpext.WipeHandler(self._mailer, self._save_dir))
        r.append('wipe-world-backups', httpext.WipeHandler(self._mailer, self._world_dir + '/backups'))
        r.append('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir))
        r.append('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir))
        r.append('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir))
        r.pop()
        r.append('log', httpext.FileSystemHandler(self._world_dir + '/server-console.txt'))
        r.push('logs', httpext.FileSystemHandler(self._logs_dir))
        r.append('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'))
        r.pop()
        r.push('backups', httpext.FileSystemHandler(self._backups_dir))
        r.append('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'))
        r.pop()
        r.push('config')
        r.append('db', httpext.FileSystemHandler(self._player_dir + '/' + _WORLD + '.db'))
        r.append('jvm', httpext.FileSystemHandler(self._runtime_dir + '/ProjectZomboid64.json'))
        config_pre = self._config_dir + '/' + _WORLD
        r.append('ini', httpext.FileSystemHandler(config_pre + '.ini'))
        r.append('sandbox', httpext.FileSystemHandler(config_pre + '_SandboxVars.lua'))
        r.append('spawnpoints', httpext.FileSystemHandler(config_pre + '_spawnpoints.lua'))
        r.append('spawnregions', httpext.FileSystemHandler(config_pre + '_spawnregions.lua'))
        r.append('shop', httpext.FileSystemHandler(self._lua_dir + '/ServerPointsListings.ini'))

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._player_dir)
        await io.create_directory(self._config_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._lua_dir)
