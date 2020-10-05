import typing
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

    def world_dir(self):
        return self._world_dir

    def executable(self):
        return self._executable

    async def initialise(self):
        await self._build_world()
        self._mailer.register(msgext.TimeoutSubscriber(self._mailer, msgext.SetSubscriber(
            proch.ShellJob(self._mailer),
            msgext.MonitorSubscriber(
                self._mailer, _ArchiveSubscriber(self._mailer, self), msgext.MonitorReply.AT_START),
            msgext.MonitorSubscriber(
                self._mailer, _WipeSubscriber(self._mailer, self), msgext.MonitorReply.AT_END)
        )))

    def resources(self, resource: httpabc.Resource):
        conf_pre = self._config_dir + '/' + self._world_name
        httpext.ResourceBuilder(resource) \
            .push('deployment', _Handler(self)) \
            .append('{command}', _CommandHandler(self._mailer, self)) \
            .pop() \
            .push('config') \
            .append('jvm', httpext.ReadWriteFileHandler(self._jvm_config_file)) \
            .append('db', httpext.ReadWriteFileHandler(self._playerdb_file, protected=True, text=False)) \
            .append('ini', httpext.ProtectedLineConfigHandler(conf_pre + '.ini', ('.*Password.*', '.*Token.*'))) \
            .append('sandbox', httpext.ReadWriteFileHandler(conf_pre + '_SandboxVars.lua')) \
            .append('spawnpoints', httpext.ReadWriteFileHandler(conf_pre + '_spawnpoints.lua')) \
            .append('spawnregions', httpext.ReadWriteFileHandler(conf_pre + '_spawnregions.lua'))

    async def _build_world(self):
        await util.create_directory(self._world_dir)
        await util.create_directory(self._playerdb_dir)
        await util.create_directory(self._config_dir)
        await util.create_directory(self._save_dir)

    async def directory_list(self) -> typing.List[typing.Dict[str, str]]:
        return await util.directory_list_dict(self._home_dir)

    async def backup_runtime(self, logger=None) -> str:
        return await util.archive_directory(self._runtime_dir, logger)

    async def backup_world(self, logger=None) -> str:
        return await util.archive_directory(self._world_dir, logger)

    async def wipe_world_all(self):
        await util.delete_directory(self._world_dir)
        await self._build_world()

    async def wipe_world_playerdb(self):
        await util.wipe_directory(self._playerdb_dir)

    async def wipe_world_config(self):
        await util.wipe_directory(self._config_dir)

    async def wipe_world_save(self):
        await util.wipe_directory(self._save_dir)

    async def handle_command(self, data: httpabc.ABC_DATA_POST) -> typing.Any:
        messenger = msgext.SynchronousMessenger(self._mailer)
        source = util.obj_to_str(messenger)
        command = str(util.get('command', data))
        if command == 'install-runtime':
            if util.get('wipe', data, True):
                await util.delete_directory(self._runtime_dir)
            script = shell.Script() \
                .include_steamcmd_app_update(
                    app_id=380870,
                    install_dir=self._runtime_dir,
                    beta=util.script_escape(util.get('beta', data)),
                    validate=util.get('validate', data)) \
                .include_softlink_steamclient_lib(self._runtime_dir) \
                .build()
            url = await httpsubs.HttpSubscriptionService.subscribe(self._mailer, source, httpsubs.Selector(
                msg_filter=msgftr.And(msgftr.SourceIs(source), proch.ShellJob.FILTER_STDOUT_LINE),
                completed_filter=msgftr.And(msgftr.SourceIs(source), proch.ShellJob.FILTER_JOB_DONE),
                aggregator=aggtrf.StrJoin('\n')))
            response = await messenger.request(source, proch.ShellJob.START_JOB, script)
            return response.data() if isinstance(response.data(), Exception) else {'url': url}
        elif command == 'backup-world' or command == 'backup-runtime':
            msg_filter = msgftr.And(msgftr.SourceIs(source), msgftr.NameIs(msgext.LoggingPublisher.INFO))
            completed_filter = msgftr.And(msg_filter, msgftr.DataStrContains('Archive created'))
            url = await httpsubs.HttpSubscriptionService.subscribe(self._mailer, source, httpsubs.Selector(
                msg_filter=msg_filter, completed_filter=completed_filter, aggregator=aggtrf.StrJoin('\n')))
            response = await messenger.request(source, _ArchiveSubscriber.REQUEST, command)
            return response.data() if isinstance(response.data(), Exception) else {'url': url}
        elif command.startswith('wipe'):
            response = await messenger.request(source, _WipeSubscriber.REQUEST, command)
            return response.data()
        return False


class _ArchiveSubscriber(msgabc.Subscriber):
    REQUEST = 'ArchiveSubscriber.Request'
    FILTER = msgftr.NameIs(REQUEST)

    def __init__(self, mailer: msgabc.Mailer, deployment: Deployment):
        self._mailer = mailer
        self._deployment = deployment

    def accepts(self, message):
        return _ArchiveSubscriber.FILTER.accepts(message)

    async def handle(self, message):
        command = message.data()
        logger = msgext.LoggingPublisher(self._mailer, message.source())
        if command == 'backup-world':
            await self._deployment.backup_world(logger)
        if command == 'backup-runtime':
            await self._deployment.backup_runtime(logger)
        return None


class _WipeSubscriber(msgabc.Subscriber):
    REQUEST, RESPONSE = 'WipeSubscriber.Request', 'WipeSubscriber.Response'
    FILTER = msgftr.NameIs(REQUEST)

    def __init__(self, mailer: msgabc.Mailer, deployment: Deployment):
        self._mailer = mailer
        self._deployment = deployment

    def accepts(self, message):
        return _WipeSubscriber.FILTER.accepts(message)

    async def handle(self, message):
        response, command = True, message.data()
        if command == 'wipe-world-all':
            await self._deployment.wipe_world_all()
        elif command == 'wipe-world-playerdb':
            await self._deployment.wipe_world_playerdb()
        elif command == 'wipe-world-config':
            await self._deployment.wipe_world_config()
        elif command == 'wipe-world-save':
            await self._deployment.wipe_world_save()
        else:
            response = False
        self._mailer.post(self, _WipeSubscriber.RESPONSE, response, message)
        return None


class _CommandHandler(httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, deployment: Deployment):
        self._mailer = mailer
        self._deployment = deployment

    async def handle_post(self, resource, data):
        result = await self._deployment.handle_command(data)
        if result is False:
            return httpabc.ResponseBody.NOT_FOUND
        if result is True:
            return httpabc.ResponseBody.NO_CONTENT
        if isinstance(result, Exception):
            return {'error': str(result)}
        return result


class _Handler(httpabc.AsyncGetHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_get(self, resource, data):
        return await self._deployment.directory_list()
