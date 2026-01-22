import socket
import aiohttp
# ALLOW core.* hytale.messaging
from core.util import util, tasks, io, aggtrf, pack, shellutil
from core.msg import msgabc, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.proc import proch
from core.common import svrhelpers
from servers.hytale import messaging as msg

LAUNCHER_EXE = 'hytale-downloader-linux-amd64'


def _default_cmdargs_settings() -> dict:
    return {}


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._launcher_exe = self._runtime_dir + '/' + LAUNCHER_EXE
        self._java_dir = self._runtime_dir + '/java'
        self._world_dir = self._home_dir + '/world'
        self._save_dir = self._world_dir + '/saves'
        self._map_file = self._save_dir + '/todo'
        self._config_dir = self._world_dir + '/config'
        self._cmdargs_settings = self._config_dir + '/cmdargs-settings.json'
        self._server_settings = self._config_dir + '/server-settings.json'

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_ports().init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/todo',
                         httpext.MtimeHandler().check(self._map_file).dir(self._save_dir))
        builder.put_installer(_InstallRuntimeHandler(self, self._context))
        builder.put_wipes(self._runtime_dir, dict(save=self._map_file, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_log(self._runtime_dir + '/todo.log').put_logs(self._runtime_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_config(dict(cmdargs=self._cmdargs_settings, server=self._server_settings))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = 'TODO'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Hytale game server not installed. Please Install Runtime first.')
        server = proch.ServerProcess(self._context, executable)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._save_dir, self._config_dir)
        if not await io.directory_exists(self._runtime_dir):
            return

    async def install_runtime(self, version: str):
        logger = msglog.LogPublisher(self._context, self)
        java_url = 'https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk'
        java_package = self._runtime_dir + '/java.tar.gz'
        launcher_url = 'https://downloader.hytale.com/hytale-downloader.zip'
        launcher_package = self._runtime_dir + '/launcher.zip'
        try:
            self._context.post(self, msg.DEPLOYMENT_START)
            logger.log('START Install')
            # await io.delete_directory(self._runtime_dir)
            # await io.create_directory(self._runtime_dir)
            logger.log(f'DOWNLOADING Java Runtime ({java_url})')
            # await self._download_url(java_url, java_package)
            logger.log('UNPACKING Java Runtime')
            await pack.unpack_targz(java_package, self._runtime_dir)
            java_unpacked = await io.directory_list(self._runtime_dir)
            java_unpacked = util.single([e['name'] for e in java_unpacked if e['name'].startswith('jdk')])
            assert java_unpacked
            await io.rename_path(self._runtime_dir + '/' + java_unpacked, self._java_dir)
            # await io.delete_file(java_package)
            logger.log(f'DOWNLOADING Hytale Launcher ({launcher_url})')
            # await self._download_url(launcher_url, launcher_package)
            logger.log('UNPACKING Hytale Launcher')
            launcher_unpacked = self._runtime_dir + '/launcher'
            await io.create_directory(launcher_unpacked)
            await pack.unpack_archive(launcher_package, launcher_unpacked)
            await io.move_path(launcher_unpacked + '/' + LAUNCHER_EXE, self._launcher_exe)
            await io.chmod(self._launcher_exe, 0o744)
            await io.delete_directory(launcher_unpacked)
            # await io.delete_file(launcher_package)
            launcher_version = await shellutil.run_executable(self._launcher_exe, '-version')
            assert launcher_version
            logger.log(f'INSTALLED Hytale Launcher: {launcher_version}')
            # INSTALL GAME HERE
            logger.log('INSTALLING ' + version)
            await self.build_world()
            logger.log('END Install')
        except Exception as e:
            logger.log(repr(e))
        finally:
            self._context.post(self, msg.DEPLOYMENT_DONE)

    async def _download_url(self, url: str, path: str):
        connector = aiohttp.TCPConnector(family=socket.AF_INET)  # force IPv4
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                                 ' AppleWebKit/537.36 (KHTML, like Gecko)'
                                 ' Chrome/120.0.0.0 Safari/537.36'}
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, read_bufsize=io.DEFAULT_CHUNK_SIZE) as response:
                print(f'STATUS {response.status}')
                assert response.status == 200
                tracker, content_length = io.NullBytesTracker(), response.headers.get('Content-Length')
                if content_length:
                    content_length = int(content_length)
                    if content_length > 52428800:
                        tracker = msglog.PercentTracker(self._context, content_length, prefix='downloaded')
                await io.stream_write_file(
                    path, io.WrapReader(response.content), io.DEFAULT_CHUNK_SIZE, self._tempdir, tracker)


class _InstallRuntimeHandler(httpabc.PostHandler):

    def __init__(self, deployment: Deployment, mailer: msgabc.MulticastMailer):
        self._mailer, self._deployment = mailer, deployment

    async def handle_post(self, resource, data):
        subscription_path = await httpsubs.HttpSubscriptionService.subscribe(
            self._mailer, self, httpsubs.Selector(
                msg_filter=msglog.LogPublisher.LOG_FILTER,
                completed_filter=msg.FILTER_DEPLOYMENT_DONE,
                aggregator=aggtrf.StrJoin('\n')))
        version = util.get('beta', data, 'TODO')
        tasks.task_fork(self._deployment.install_runtime(version), 'hytale.install_runtime()')
        url = util.get('baseurl', data, '') + subscription_path
        return dict(url=url)
