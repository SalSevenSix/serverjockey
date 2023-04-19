from core.util import io
from core.msg import msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpstm
from core.proc import proch, jobh
from core.system import interceptors as x

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
        # TODO consider r.push_interceptor() to decorate somehow
        m = self._mailer
        r = httprsc.ResourceBuilder(resource)
        r.psh('deployment')
        r.add('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_380870.acf'))
        r.add('install-runtime', x.snr(m, httpstm.SteamCmdInstallHandler(m, self._runtime_dir, 380870)))
        r.add('wipe-runtime', x.snr(m, httpext.WipeHandler(m, self._runtime_dir)))
        r.add('wipe-world-all', x.snr(m, httpext.WipeHandler(m, self._world_dir)))
        r.add('wipe-world-playerdb', x.snr(m, httpext.WipeHandler(m, self._player_dir)))
        r.add('wipe-world-config', x.snr(m, httpext.WipeHandler(m, self._config_dir)))
        r.add('wipe-world-save', x.snr(m, httpext.WipeHandler(m, self._save_dir)))
        r.add('wipe-world-backups', x.snr(m, httpext.WipeHandler(m, self._world_dir + '/backups')))
        r.add('backup-runtime', x.snr(m, httpext.ArchiveHandler(m, self._backups_dir, self._runtime_dir)))
        r.add('backup-world', x.snr(m, httpext.ArchiveHandler(m, self._backups_dir, self._world_dir)))
        r.add('restore-backup', x.snr(m, httpext.UnpackerHandler(m, self._backups_dir, self._home_dir)))
        r.pop()
        r.add('log', httpext.FileSystemHandler(self._world_dir + '/server-console.txt'))
        r.psh('logs', httpext.FileSystemHandler(self._logs_dir))
        r.add('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'))
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.add('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'))
        r.pop()
        r.psh('config')
        r.add('db', x.snr(m, httpext.FileSystemHandler(self._player_dir + '/' + _WORLD + '.db')))
        r.add('jvm', httpext.FileSystemHandler(self._runtime_dir + '/ProjectZomboid64.json'))
        config_pre = self._config_dir + '/' + _WORLD
        r.add('ini', httpext.FileSystemHandler(config_pre + '.ini'))
        r.add('sandbox', httpext.FileSystemHandler(config_pre + '_SandboxVars.lua'))
        r.add('spawnpoints', httpext.FileSystemHandler(config_pre + '_spawnpoints.lua'))
        r.add('spawnregions', httpext.FileSystemHandler(config_pre + '_spawnregions.lua'))
        r.add('shop', httpext.FileSystemHandler(self._lua_dir + '/ServerPointsListings.ini'))

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._player_dir)
        await io.create_directory(self._config_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._lua_dir)
