import logging
from core.util import aggtrf, util, io
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.proc import proch, shell
from core.system import svrext


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._world_name = 'servertest'
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
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
            svrext.ServerRunningLock(self._mailer, proch.JobProcess(self._mailer)),
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
            .append('install-runtime', _InstallRuntimeHandler(self._mailer, self._runtime_dir)) \
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


class _InstallRuntimeHandler(httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, path: str):
        self._mailer = mailer
        self._path = path
        self._handler = httpext.MessengerHandler(self._mailer, proch.JobProcess.START, selector=httpsubs.Selector(
            msg_filter=proch.JobProcess.FILTER_STDOUT_LINE,
            completed_filter=proch.JobProcess.FILTER_JOB_DONE,
            aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        script = shell.Script()
        if util.get('wipe', data):
            script.include_delete_path(self._path)
        script.include_steamcmd_app_update(
            app_id=380870,
            install_dir=self._path,
            beta=util.script_escape(util.get('beta', data)),
            validate=util.get('validate', data))
        script.include_softlink_steamclient_lib(self._path)
        script = script.build()
        logging.debug('SCRIPT\n' + script)
        data['script'] = script
        return await self._handler.handle_post(resource, data)


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
