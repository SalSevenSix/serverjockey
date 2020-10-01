import asyncio
import typing
from core import contextsvc, util, shell, httpabc


class Deployment:

    def __init__(self, context: contextsvc.Context):
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
        self._build_world()

    def handler(self) -> httpabc.GetHandler:
        return _Handler(self)

    def command_handler(self) -> httpabc.AsyncPostHandler:
        return _CommandHandler(self)

    def directory_list(self) -> typing.List[typing.Dict[str, str]]:
        return util.directory_list_dict(self.home_dir)

    async def install_runtime(self,
                              beta: typing.Optional[str] = None,
                              validate: bool = False,
                              wipe: bool = True) -> str:
        if wipe:
            util.delete_directory(self.runtime_dir)
        script = shell.Script() \
            .include_steamcmd_app_update(
                app_id=380870,
                install_dir=self.runtime_dir,
                beta=beta,
                validate=validate) \
            .include_softlink_steamclient_lib(self.runtime_dir) \
            .build()
        process = await asyncio.create_subprocess_shell(
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL)
        stdout, stderr = await process.communicate()
        result = [stdout.decode()] if stdout else ['NO STDOUT']
        result.append('EXIT STATUS: ' + str(process.returncode))
        return '\n'.join(result)   # TODO give a httpsub link back instead

    def backup_runtime(self) -> str:
        return util.archive_directory(self.runtime_dir)

    def backup_world(self) -> str:
        return util.archive_directory(self.world_dir)

    def wipe_world_all(self):
        util.delete_directory(self.world_dir)
        self._build_world()

    def wipe_world_playerdb(self):
        util.wipe_directory(self.playerdb_dir)

    def wipe_world_config(self):
        util.wipe_directory(self.config_dir)

    def wipe_world_save(self):
        util.wipe_directory(self.save_dir)

    def _build_world(self):
        util.create_directory(self.world_dir)
        util.create_directory(self.playerdb_dir)
        util.create_directory(self.config_dir)
        util.create_directory(self.save_dir)


class _Handler(httpabc.GetHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    def handle_get(self, resource, data):
        return self._deployment.directory_list()


class _CommandHandler(httpabc.AsyncPostHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_post(self, resource, data):
        command = util.get('command', data)
        if command == 'backup-world':
            return {'file': self._deployment.backup_world()}
        if command == 'wipe-world-all':
            self._deployment.wipe_world_all()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-playerdb':
            self._deployment.wipe_world_playerdb()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-config':
            self._deployment.wipe_world_config()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'wipe-world-save':
            self._deployment.wipe_world_save()
            return httpabc.ResponseBody.NO_CONTENT
        if command == 'backup-runtime':
            return {'file': self._deployment.backup_runtime()}
        if command == 'install-runtime':
            return await self._deployment.install_runtime(
                beta=util.script_escape(util.get('beta', data)),
                validate=util.get('validate', data))
        return httpabc.ResponseBody.NOT_FOUND
