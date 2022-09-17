from core.util import aggtrf, util, io
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpstm, httpsubs
from core.proc import proch, jobh
from core.system import svrext


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._world_name = 'servertest'
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._runtime_metafile = self._runtime_dir + '/steamapps/appmanifest_380870.acf'
        self._executable = self._runtime_dir + '/start-server.sh'
        self._jvm_config_file = self._runtime_dir + '/ProjectZomboid64.json'
        self._world_dir = self._home_dir + '/world'
        self._playerdb_dir = self._world_dir + '/db'
        self._playerdb_file = self._playerdb_dir + '/' + self._world_name + '.db'
        self._console_log = self._world_dir + '/server-console.txt'
        self._logs_dir = self._world_dir + '/Logs'
        self._config_dir = self._world_dir + '/Server'
        self._save_dir = self._world_dir + '/Saves'

    def new_server_process(self):
        return proch.ServerProcess(self._mailer, self._executable).append_arg('-cachedir=' + self._world_dir)

    async def initialise(self):
        await self.build_world()
        self._mailer.register(msgext.TimeoutSubscriber(self._mailer, msgext.SetSubscriber(
            svrext.ServerRunningLock(self._mailer, jobh.JobProcess(self._mailer)),
            msgext.SyncWrapper(self._mailer, msgext.ReadWriteFileSubscriber(self._mailer), msgext.SyncReply.AT_END),
            svrext.ServerRunningLock(
                self._mailer,
                msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer), msgext.SyncReply.AT_START)),
            svrext.ServerRunningLock(
                self._mailer,
                msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer), msgext.SyncReply.AT_START)),
            svrext.ServerRunningLock(
                self._mailer,
                msgext.SyncWrapper(self._mailer, _DeploymentWiper(self), msgext.SyncReply.AT_END))
        )))

    def resources(self, resource: httpabc.Resource):
        ini_filter = ('.*Password.*', '.*Token.*')
        conf_pre = self._config_dir + '/' + self._world_name
        archive_selector = httpsubs.Selector(
            msg_filter=msgftr.NameIs(msgext.LoggingPublisher.INFO),
            completed_filter=msgftr.DataEquals('END Archive Directory'),
            aggregator=aggtrf.StrJoin('\n'))
        unpacker_selector = httpsubs.Selector(
            msg_filter=msgftr.NameIs(msgext.LoggingPublisher.INFO),
            completed_filter=msgftr.DataEquals('END Unpack Directory'),
            aggregator=aggtrf.StrJoin('\n'))
        httprsc.ResourceBuilder(resource) \
            .push('deployment') \
            .append('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile)) \
            .append('install-runtime', httpstm.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 380870)) \
            .append('wipe-runtime', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._runtime_dir})) \
            .append('backup-runtime', httpext.MessengerHandler(
                self._mailer, msgext.Archiver.REQUEST,
                {'backups_dir': self._backups_dir, 'source_dir': self._runtime_dir}, archive_selector)) \
            .append('backup-world', httpext.MessengerHandler(
                self._mailer, msgext.Archiver.REQUEST,
                {'backups_dir': self._backups_dir, 'source_dir': self._world_dir}, archive_selector)) \
            .append('restore-backup', httpext.MessengerHandler(
                self._mailer, msgext.Unpacker.REQUEST,
                {'backups_dir': self._backups_dir, 'root_dir': self._home_dir}, unpacker_selector)) \
            .append('wipe-world-all', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._world_dir})) \
            .append('wipe-world-playerdb', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._playerdb_dir})) \
            .append('wipe-world-config', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._config_dir})) \
            .append('wipe-world-save', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._save_dir})) \
            .pop() \
            .append('log', httpext.FileSystemHandler(self._console_log)) \
            .push('logs', httpext.FileSystemHandler(self._logs_dir)) \
            .append('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path')) \
            .pop() \
            .push('backups', httpext.FileSystemHandler(self._backups_dir)) \
            .append('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path')) \
            .pop() \
            .push('config') \
            .append('db', httpext.FileSystemHandler(self._playerdb_file)) \
            .append('jvm', httpext.MessengerConfigHandler(self._mailer, self._jvm_config_file)) \
            .append('ini', httpext.MessengerConfigHandler(self._mailer, conf_pre + '.ini', ini_filter)) \
            .append('sandbox', httpext.MessengerConfigHandler(self._mailer, conf_pre + '_SandboxVars.lua')) \
            .append('spawnpoints', httpext.MessengerConfigHandler(self._mailer, conf_pre + '_spawnpoints.lua')) \
            .append('spawnregions', httpext.MessengerConfigHandler(self._mailer, conf_pre + '_spawnregions.lua'))

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._playerdb_dir)
        await io.create_directory(self._config_dir)
        await io.create_directory(self._save_dir)


class _DeploymentWiper(msgabc.AbcSubscriber):
    REQUEST = 'DeploymentWiper.Request'

    def __init__(self, deployment: Deployment):
        super().__init__(msgftr.NameIs(_DeploymentWiper.REQUEST))
        self._deployment = deployment

    async def handle(self, message):
        path = util.get('path', message.data())
        await io.delete_directory(path)
        await self._deployment.build_world()
        return None
