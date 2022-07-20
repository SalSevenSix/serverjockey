import aiohttp
from core.util import util
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._install_package = self._home_dir + '/factorio.tar.xz'
        self._runtime_dir = self._home_dir + '/runtime'
        self._executable = self._runtime_dir + '/bin/x64/factorio'
        self._server_settings_def = self._runtime_dir + '/data/server-settings.example.json'
        self._map_settings_def = self._runtime_dir + '/data/map-settings.example.json'
        self._map_gen_settings_def = self._runtime_dir + '/data/map-gen-settings.example.json'
        self._world_dir = self._home_dir + '/world'
        self._save_dir = self._world_dir + '/saves'
        self._map_file = self._save_dir + '/map.zip'
        self._config_dir = self._world_dir + '/config'
        self._server_settings = self._config_dir + '/server-settings.json'
        self._map_settings = self._config_dir + '/map-settings.json'
        self._map_gen_settings = self._config_dir + '/map-gen-settings.json'

    async def initialise(self):
        await self.build_world()
        self._mailer.register(proch.JobProcess(self._mailer))

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('config') \
            .append('server', httpext.FileSystemHandler(self._server_settings)) \
            .append('map', httpext.FileSystemHandler(self._map_settings)) \
            .append('mapgen', httpext.FileSystemHandler(self._map_gen_settings)) \
            .pop() \
            .push('deployment') \
            .append('install-runtime', _InstallRuntimeHandler(self)) \
            .append('create-map', _CreateMapHandler(self)) \
            .append('wipe-world-all', _WipeHandler(self, self._world_dir)) \
            .append('wipe-world-config', _WipeHandler(self, self._save_dir)) \
            .append('wipe-world-save', _WipeHandler(self, self._config_dir))

    def new_server_process(self):
        return proch.ServerProcess(self._mailer, self._executable) \
            .append_arg('--start-server').append_arg(self._map_file) \
            .append_arg('--server-settings').append_arg(self._server_settings)

    async def install_runtime(self):
        url = 'https://factorio.com/get-download/stable/headless/linux64'
        unpack_dir, chunk_size = self._home_dir + '/factorio', 65536
        await util.delete_file(self._install_package)
        await util.delete_directory(unpack_dir)
        await util.delete_directory(self._runtime_dir)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, read_bufsize=chunk_size) as response:
                assert response.status == 200
                await util.stream_write_file(self._install_package, response.content, chunk_size)
        await util.unpack_tarxz(self._install_package, self._home_dir)
        await util.rename_path(unpack_dir, self._runtime_dir)
        await util.delete_file(self._install_package)
        await self.build_world()

    async def create_map(self):
        await util.delete_directory(self._save_dir)
        await util.create_directory(self._save_dir)
        await proch.JobProcess.start_job(self._mailer, self, (
            self._executable,
            '--create', self._map_file,
            '--map-gen-settings', self._map_gen_settings,
            '--map-settings', self._map_settings
        ))

    async def build_world(self):
        await util.create_directory(self._world_dir)
        await util.create_directory(self._save_dir)
        await util.create_directory(self._config_dir)
        if await util.directory_exists(self._runtime_dir):
            if not await util.file_exists(self._server_settings):
                await util.copy_text_file(self._server_settings_def, self._server_settings)
            if not await util.file_exists(self._map_settings):
                await util.copy_text_file(self._map_settings_def, self._map_settings)
            if not await util.file_exists(self._map_gen_settings):
                await util.copy_text_file(self._map_gen_settings_def, self._map_gen_settings)


class _InstallRuntimeHandler(httpabc.AsyncPostHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_post(self, resource, data):
        await self._deployment.install_runtime()
        return httpabc.ResponseBody.NO_CONTENT


class _CreateMapHandler(httpabc.AsyncPostHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_post(self, resource, data):
        await self._deployment.create_map()
        return httpabc.ResponseBody.NO_CONTENT


class _WipeHandler(httpabc.AsyncPostHandler):

    def __init__(self, deployment: Deployment, path: str):
        self._deployment = deployment
        self._path = path

    async def handle_post(self, resource, data):
        await util.delete_directory(self._path)
        await self._deployment.build_world()
        return httpabc.ResponseBody.NO_CONTENT
