import socket
import aiohttp
# ALLOW core.* teamspeak.messaging
from core.util import gc, util, tasks, io, pack, aggtrf
from core.msg import msgabc, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.proc import proch
from core.common import portmapper, svrhelpers
from servers.teamspeak import messaging as msg

_DEFAULT_VOICE_PORT, _DEFAULT_FILE_PORT = 9987, 30033
_DEFAULT_VERSION = '3.13.7'


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._changelog = self._runtime_dir + '/CHANGELOG.text'
        self._env = context.env()
        self._env['TS3SERVER_LICENSE'] = 'accept'

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_ports().init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._changelog, httpext.MtimeHandler().dir(self._logs_dir))
        builder.put_installer(_InstallRuntimeHandler(self, self._context))
        builder.put_wipes(self._runtime_dir, dict(all=self._world_dir, logs=self._logs_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        # builder.put_config(dict(cmdargs=self._cmdargs_settings))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/ts3server'
        if not await io.file_exists(executable):
            raise FileNotFoundError('TeamSpeak server not installed. Please Install Runtime first.')
        portmapper.map_port(self._context, self, _DEFAULT_VOICE_PORT, gc.UDP, 'TeamSpeak Voice UDP port')
        portmapper.map_port(self._context, self, _DEFAULT_FILE_PORT, gc.TCP, 'TeamSpeak File TCP port')
        return proch.ServerProcess(self._context, executable).use_cwd(self._runtime_dir).use_env(self._env)

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        logs_dir = self._runtime_dir + '/logs'
        if not await io.symlink_exists(logs_dir):
            await io.create_symlink(logs_dir, self._logs_dir)
        if not await io.symlink_exists(self._changelog):
            await io.create_symlink(self._changelog, self._changelog[:-5])

    async def install_runtime(self, version):
        logger = msglog.LogPublisher(self._context, self)
        unpack_dir = 'teamspeak3-server_linux_amd64'
        filename = '/' + unpack_dir + '-' + version + '.tar.bz2'
        install_package = self._home_dir + filename
        url = 'https://files.teamspeak-services.com/releases/server/' + version + filename
        unpack_dir = self._home_dir + '/' + unpack_dir
        try:
            self._context.post(self, msg.DEPLOYMENT_START)
            logger.log('START Install')
            await io.delete_file(install_package)
            await io.delete_directory(unpack_dir)
            await io.delete_directory(self._runtime_dir)
            logger.log(f'DOWNLOADING {url}')
            connector = aiohttp.TCPConnector(family=socket.AF_INET)  # force IPv4
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, read_bufsize=io.DEFAULT_CHUNK_SIZE) as response:
                    assert response.status == 200
                    tracker, content_length = None, response.headers.get('Content-Length')
                    if content_length:
                        tracker = msglog.PercentTracker(self._context, int(content_length), prefix='downloaded')
                    await io.stream_write_file(
                        install_package, io.WrapReader(response.content), io.DEFAULT_CHUNK_SIZE, self._tempdir, tracker)
            logger.log(f'UNPACKING {install_package}')
            await pack.unpack_tarbz(install_package, self._home_dir)
            logger.log('INSTALLING TeamSpeak server')
            await io.rename_path(unpack_dir, self._runtime_dir)
            await io.delete_file(install_package)
            await self.build_world()
            logger.log('END Install')
        except Exception as e:
            logger.log(repr(e))
        finally:
            self._context.post(self, msg.DEPLOYMENT_DONE)


class _InstallRuntimeHandler(httpabc.PostHandler):

    def __init__(self, deployment: Deployment, mailer: msgabc.MulticastMailer):
        self._mailer, self._deployment = mailer, deployment

    async def handle_post(self, resource, data):
        subscription_path = await httpsubs.HttpSubscriptionService.subscribe(
            self._mailer, self, httpsubs.Selector(
                msg_filter=msglog.LogPublisher.LOG_FILTER,
                completed_filter=msg.FILTER_DEPLOYMENT_DONE,
                aggregator=aggtrf.StrJoin('\n')))
        version = util.get('beta', data, _DEFAULT_VERSION)
        tasks.task_fork(self._deployment.install_runtime(version), 'teamspeak.install_runtime()')
        url = util.get('baseurl', data, '') + subscription_path
        return dict(url=url)
