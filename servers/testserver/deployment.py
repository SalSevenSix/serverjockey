import sys
# ALLOW core.* testserver.messaging
from core.util import util, io, objconv, pkg, dtutil
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch
from core.common import svrhelpers
from servers.testserver import messaging as msg

_MAIN_PY = 'main.py'


def default_config():
    return {
        'players': 'MrGoober,StabMasterArson,YouMadNow',
        'start_speed_modifier': 1,
        'crash_on_start_seconds': 0.0,
        'ingametime_interval_seconds': 80.0
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir, self._world_dir = self._home_dir + '/runtime', self._home_dir + '/world'
        self._executable = self._runtime_dir + '/' + _MAIN_PY
        self._runtime_metafile = self._runtime_dir + '/readme.text'
        self._logs_dir, self._config_file = self._world_dir + '/logs', self._world_dir + '/config.json'

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_archiving(self._tempdir).init_logging(self._logs_dir, msg.CONSOLE_LOG_FILTER).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_metafile, httpext.MtimeHandler().dir(self._logs_dir))
        builder.put_installer(_InstallRuntimeHandler(self))
        builder.put_wipes(self._runtime_dir, dict(config=self._config_file, logs=self._logs_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_config(dict(cmdargs=self._config_file))

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('Testserver game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._config_file))
        server = proch.ServerProcess(self._context, sys.executable).append_arg(self._executable)
        for key in cmdargs.keys():
            server.append_arg(cmdargs[key])
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir)
        await io.keyfill_json_file(self._config_file, default_config())

    async def install_runtime(self, beta: str | None):
        await io.delete_directory(self._runtime_dir)
        await io.create_directory(self._runtime_dir)
        main_py = await pkg.pkg_load('servers.testserver', _MAIN_PY)
        await io.write_file(self._executable, main_py)
        await io.write_file(self._runtime_metafile, 'build : ' + str(dtutil.now_millis()) + '\nbeta  : ' + beta)


class _InstallRuntimeHandler(httpabc.PostHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_post(self, resource, data):
        await self._deployment.install_runtime(util.get('beta', data, 'none'))
        return httpabc.ResponseBody.NO_CONTENT
