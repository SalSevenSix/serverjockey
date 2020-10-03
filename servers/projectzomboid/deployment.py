import typing
from core.util import aggtrf, util
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
        if not self._executable:
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
        proch.ShellJobService(self._mailer)
        await self._build_world()

    def resources(self, resource: httpabc.Resource):
        conf_pre = self._config_dir + '/' + self._world_name
        httpext.ResourceBuilder(resource) \
            .push('deployment', _Handler(self)) \
            .append('{command}', _CommandHandler(self)) \
            .pop() \
            .push('config') \
            .append('jvm', httpext.ReadWriteFileHandler(self._jvm_config_file)) \
            .append('db', httpext.ReadWriteFileHandler(self._playerdb_file, protected=True, text=False)) \
            .append('ini', httpext.ProtectedLineConfigHandler(conf_pre + '.ini', ('.*Password.*', '.*Token.*'))) \
            .append('sandbox', httpext.ReadWriteFileHandler(conf_pre + '_SandboxVars.lua')) \
            .append('spawnpoints', httpext.ReadWriteFileHandler(conf_pre + '_spawnpoints.lua')) \
            .append('spawnregions', httpext.ReadWriteFileHandler(conf_pre + '_spawnregions.lua'))

    async def directory_list(self) -> typing.List[typing.Dict[str, str]]:
        return await util.directory_list_dict(self._home_dir)

    async def install_runtime(self,
                              beta: typing.Optional[str] = None,
                              validate: bool = False,
                              wipe: bool = True) -> dict:
        if wipe:
            await util.delete_directory(self._runtime_dir)
        script = shell.Script() \
            .include_steamcmd_app_update(
                app_id=380870,
                install_dir=self._runtime_dir,
                beta=beta,
                validate=validate) \
            .include_softlink_steamclient_lib(self._runtime_dir) \
            .build()
        response = await proch.ShellJobService.start_job(self._mailer, self, script)
        if isinstance(response, Exception):
            return {'exception': repr(response)}
        url = await httpsubs.HttpSubscriptionService.subscribe(self._mailer, self, httpsubs.Selector(
            msg_filter=proch.ShellJobService.FILTER_STDOUT_LINE,
            completed_filter=proch.ShellJobService.FILTER_JOB_DONE,
            aggregator=aggtrf.StrJoin('\n')))
        return {'url': url}

    async def backup_runtime(self) -> str:
        return await util.archive_directory(self._runtime_dir)

    async def backup_world(self) -> str:
        return await util.archive_directory(self._world_dir)

    async def wipe_world_all(self):
        await util.delete_directory(self._world_dir)
        await self._build_world()

    async def wipe_world_playerdb(self):
        await util.wipe_directory(self._playerdb_dir)

    async def wipe_world_config(self):
        await util.wipe_directory(self._config_dir)

    async def wipe_world_save(self):
        await util.wipe_directory(self._save_dir)

    async def _build_world(self):
        await util.create_directory(self._world_dir)
        await util.create_directory(self._playerdb_dir)
        await util.create_directory(self._config_dir)
        await util.create_directory(self._save_dir)


class _Handler(httpabc.GetHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_get(self, resource, data):
        return await self._deployment.directory_list()


class _CommandHandler(httpabc.AsyncPostHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    # TODO everything called here should be serialised with lock
    #      ie. attempting concurrent request returns error if job still running
    async def handle_post(self, resource, data):
        command = util.get('command', data)
        if command == 'backup-world':
            file = await self._deployment.backup_world()
            return {'file': file}
        if command == 'wipe-world-all':
            await self._deployment.wipe_world_all()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-playerdb':
            await self._deployment.wipe_world_playerdb()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-config':
            await self._deployment.wipe_world_config()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-save':
            await self._deployment.wipe_world_save()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'backup-runtime':
            file = await self._deployment.backup_runtime()
            return {'file': file}
        if command == 'install-runtime':
            return await self._deployment.install_runtime(
                beta=util.script_escape(util.get('beta', data)),
                validate=util.get('validate', data))
        return httpabc.ResponseBody.NOT_FOUND
