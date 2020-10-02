import typing
from core.util import aggtrf, util
from core.context import contextsvc
from core.http import httpabc, httpsubs
from core.proc import proch, shell


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self.world_name = 'servertest'
        self.home_dir = context.config('home')
        self.runtime_dir = self.home_dir + '/runtime'
        self.executable = util.overridable_full_path(self.home_dir, context.config('executable'))
        if not self.executable:
            self.executable = self.runtime_dir + '/start-server.sh'
        self.jvm_config_file = self.runtime_dir + '/ProjectZomboid64.json'
        self.world_dir = self.home_dir + '/world'
        self.playerdb_dir = self.world_dir + '/db'
        self.playerdb_file = self.playerdb_dir + '/' + self.world_name + '.db'
        self.config_dir = self.world_dir + '/Server'
        self.save_dir = self.world_dir + '/Saves'
        proch.ShellJobService(context)

    async def initialise(self):
        await self._build_world()

    def handler(self) -> httpabc.GetHandler:
        return _Handler(self)

    def command_handler(self) -> httpabc.AsyncPostHandler:
        return _CommandHandler(self)

    async def directory_list(self) -> typing.List[typing.Dict[str, str]]:
        return await util.directory_list_dict(self.home_dir)

    async def install_runtime(self,
                              beta: typing.Optional[str] = None,
                              validate: bool = False,
                              wipe: bool = True) -> dict:
        if wipe:
            await util.delete_directory(self.runtime_dir)
        script = shell.Script() \
            .include_steamcmd_app_update(
                app_id=380870,
                install_dir=self.runtime_dir,
                beta=beta,
                validate=validate) \
            .include_softlink_steamclient_lib(self.runtime_dir) \
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
        return await util.archive_directory(self.runtime_dir)

    async def backup_world(self) -> str:
        return await util.archive_directory(self.world_dir)

    async def wipe_world_all(self):
        await util.delete_directory(self.world_dir)
        await self._build_world()

    async def wipe_world_playerdb(self):
        await util.wipe_directory(self.playerdb_dir)

    async def wipe_world_config(self):
        await util.wipe_directory(self.config_dir)

    async def wipe_world_save(self):
        await util.wipe_directory(self.save_dir)

    async def _build_world(self):
        await util.create_directory(self.world_dir)
        await util.create_directory(self.playerdb_dir)
        await util.create_directory(self.config_dir)
        await util.create_directory(self.save_dir)


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
