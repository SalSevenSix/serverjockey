from core.util import aggtrf, util
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httpsubs, httpext
from core.proc import proch, shell


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._world_name = 'servertest'
        self._home_dir = context.config('home')
        self._runtime_dir = self._home_dir + '/runtime'
        self._executable = util.overridable_full_path(self._home_dir, context.config('executable'))
        if self._executable is None:
            self._executable = self._runtime_dir + '/start-server.sh'
        self._jvm_config_file = self._runtime_dir + '/ProjectZomboid64.json'
        self._world_dir = self._home_dir + '/world'
        self._playerdb_dir = self._world_dir + '/db'
        self._playerdb_file = self._playerdb_dir + '/' + self._world_name + '.db'
        self._config_dir = self._world_dir + '/Server'
        self._save_dir = self._world_dir + '/Saves'

    def new_server_process(self):
        return proch.ServerProcess(self._mailer, self._executable).append_arg('-cachedir=' + self._world_dir)

    async def initialise(self):
        await self.build_world()
        self._mailer.register(msgext.TimeoutSubscriber(self._mailer, msgext.SetSubscriber(
            proch.ShellJob(self._mailer),
            msgext.DelegateSubscriber(
                self._mailer, msgext.ReadWriteFileSubscriber(self._mailer), msgext.DelegateReply.AT_END),
            msgext.DelegateSubscriber(
                self._mailer, msgext.Archiver(self._mailer), msgext.DelegateReply.AT_START),
            msgext.DelegateSubscriber(
                self._mailer, _DeploymentWiper(self), msgext.DelegateReply.AT_END)
        )))

    def resources(self, resource: httpabc.Resource):
        conf_pre = self._config_dir + '/' + self._world_name
        archive_selector = httpsubs.Selector(
            msg_filter=msgftr.NameIs(msgext.LoggingPublisher.INFO),
            completed_filter=msgftr.DataStrContains('Archive created'),
            aggregator=aggtrf.StrJoin('\n'))
        httpext.ResourceBuilder(resource) \
            .push('deployment', httpext.DirectoryListHandler(self._home_dir)) \
            .append('install-runtime', _InstallRuntimeHandler(self._mailer, self._runtime_dir)) \
            .append('backup-runtime', httpext.MessengerHandler(
                self._mailer, msgext.Archiver.REQUEST, {'path': self._runtime_dir}, archive_selector)) \
            .append('backup-world', httpext.MessengerHandler(
                self._mailer, msgext.Archiver.REQUEST, {'path': self._world_dir}, archive_selector)) \
            .append('wipe-world-all', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._world_dir})) \
            .append('wipe-world-playerdb', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._playerdb_dir})) \
            .append('wipe-world-config', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._config_dir})) \
            .append('wipe-world-save', httpext.MessengerHandler(
                self._mailer, _DeploymentWiper.REQUEST, {'path': self._save_dir})) \
            .pop() \
            .push('config') \
            .append('jvm', httpext.FileHandler(self._mailer, self._jvm_config_file)) \
            .append('db', httpext.FileHandler(self._mailer, self._playerdb_file, protected=True, text=False)) \
            .append('ini', httpext.ConfigHandler(self._mailer, conf_pre + '.ini', ('.*Password.*', '.*Token.*'))) \
            .append('sandbox', httpext.FileHandler(self._mailer, conf_pre + '_SandboxVars.lua')) \
            .append('spawnpoints', httpext.FileHandler(self._mailer, conf_pre + '_spawnpoints.lua')) \
            .append('spawnregions', httpext.FileHandler(self._mailer, conf_pre + '_spawnregions.lua'))

    async def build_world(self):
        await util.create_directory(self._world_dir)
        await util.create_directory(self._playerdb_dir)
        await util.create_directory(self._config_dir)
        await util.create_directory(self._save_dir)


class _InstallRuntimeHandler(httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, path: str):
        self._mailer = mailer
        self._path = path
        self._handler = httpext.MessengerHandler(self._mailer, proch.ShellJob.START_JOB, selector=httpsubs.Selector(
                msg_filter=proch.ShellJob.FILTER_STDOUT_LINE,
                completed_filter=proch.ShellJob.FILTER_JOB_DONE,
                aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        script = shell.Script() \
            .include_steamcmd_app_update(
                app_id=380870,
                install_dir=self._path,
                beta=util.script_escape(util.get('beta', data)),
                validate=util.get('validate', data)) \
            .include_softlink_steamclient_lib(self._path) \
            .build()
        return await self._handler.handle_post(resource, script)


class _DeploymentWiper(msgabc.AbcSubscriber):
    REQUEST = 'DeploymentWiper.Request'

    def __init__(self, deployment: Deployment):
        super().__init__(msgftr.NameIs(_DeploymentWiper.REQUEST))
        self._deployment = deployment

    async def handle(self, message):
        path = util.get('path', message.data())
        await util.delete_directory(path)
        await self._deployment.build_world()
        return None
