import socket
import asyncio
import aiohttp
# ALLOW core.* hytale.messaging
from core.util import util, tasks, io, aggtrf, pack, shellutil, funcutil
from core.msg import msgabc, msglog, msgpipe
from core.context import contextsvc
from core.http import httpabc, httprsc, httpsubs
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
        self._java_exe = self._java_dir + '/bin/java'
        self._server_dir = self._runtime_dir + '/server'
        self._server_aot = self._server_dir + '/Server/HytaleServer.aot'
        self._server_jar = self._server_dir + '/Server/HytaleServer.jar'
        self._world_dir = self._home_dir + '/world'

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_ports().init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        # builder.put_meta(self._runtime_dir + '/xyz',
        #                  httpext.MtimeHandler().check(self._map_file).dir(self._save_dir))
        builder.put_installer(_InstallRuntimeHandler(self, self._context))
        # builder.put_wipes(self._runtime_dir, dict(save=self._map_file, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_log(self._runtime_dir + '/todo.log').put_logs(self._runtime_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        # builder.put_config(dict(cmdargs=self._cmdargs_settings))

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._server_jar):
            raise FileNotFoundError('Hytale game server not installed. Please Install Runtime first.')
        server = proch.ServerProcess(self._context, self._java_exe).use_cwd(self._world_dir)
        server.append_arg('-XX:AOTCache=' + self._server_aot)
        server.append_arg('-jar').append_arg(self._server_jar)
        server.append_arg('--assets').append_arg(self._server_dir + '/Assets.zip')
        server.append_arg('--universe').append_arg(self._world_dir)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir)
        if not await io.directory_exists(self._runtime_dir):
            return

    async def install_runtime(self, version: str):
        logger = msglog.LogPublisher(self._context, self)
        try:
            self._context.post(self, msg.DEPLOYMENT_START)
            logger.log('START Install')
            await io.delete_directory(self._runtime_dir)
            await io.create_directory(self._runtime_dir)
            await self._install_java(logger)
            await self._install_launcher(logger)
            server_package = await self._download_server(logger, version)
            await self._install_server(logger, server_package)
            await self.build_world()
            logger.log('END Install')
        except Exception as e:
            logger.log(repr(e))
        finally:
            self._context.post(self, msg.DEPLOYMENT_DONE)

    async def _install_java(self, logger):
        url = 'https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk'
        logger.log(f'DOWNLOADING Java ({url})')
        package = self._runtime_dir + '/java.tar.gz'
        await self._download_url(url, package)
        logger.log('UNPACKING Java')
        await pack.unpack_targz(package, self._runtime_dir)
        unpacked = await io.directory_list(self._runtime_dir)
        unpacked = util.single([e['name'] for e in unpacked if e['name'].startswith('jdk')])
        assert unpacked
        await io.rename_path(self._runtime_dir + '/' + unpacked, self._java_dir)
        await io.delete_file(package)
        version = await shellutil.run_executable(self._java_exe, '--version')
        assert version
        version = util.single(version.split('\n'))
        logger.log(f'INSTALLED Java ({version})')

    async def _install_launcher(self, logger):
        url = 'https://downloader.hytale.com/hytale-downloader.zip'
        logger.log(f'DOWNLOADING HytaleLauncher ({url})')
        package = self._runtime_dir + '/launcher.zip'
        await self._download_url(url, package)
        logger.log('UNPACKING HytaleLauncher')
        unpacked = self._runtime_dir + '/launcher'
        await io.create_directory(unpacked)
        await pack.unpack_archive(package, unpacked)
        await io.move_path(unpacked + '/' + LAUNCHER_EXE, self._launcher_exe)
        await io.chmod(self._launcher_exe, 0o744)
        await io.delete_directory(unpacked)
        await io.delete_file(package)
        version = await shellutil.run_executable(self._launcher_exe, '-version')
        assert version
        logger.log(f'INSTALLED HytaleLauncher ({version})')

    async def _download_server(self, logger, version: str) -> str:
        logger.log('DOWNLOADING HytaleServer (' + (version.strip() if version else 'release') + ')')
        stderr, stdout, package = None, None, self._server_dir + '.zip'
        args = ['-download-path', package]
        if version:
            args.append('-patchline')
            args.append(version.strip())
        try:
            logger.log('RUN ' + self._launcher_exe + ' ' + ' '.join(args))
            process = await asyncio.create_subprocess_exec(
                self._launcher_exe, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stderr = msgpipe.PipeOutLineProducer(logger.mailer(), logger.source(), logger.name(), process.stderr)
            stdout = msgpipe.PipeOutLineProducer(logger.mailer(), logger.source(), logger.name(), process.stdout)
            rc = await process.wait()
            if rc != 0:
                raise Exception(f'HytaleServer download failed (exit code {rc})')
            logger.log('DOWNLOADED HytaleServer')
            return package
        finally:
            await funcutil.silently_cleanup(stdout)
            await funcutil.silently_cleanup(stderr)

    async def _install_server(self, logger, package: str):
        logger.log('UNPACKING HytaleServer')
        await io.create_directory(self._server_dir)
        await pack.unpack_archive(package, self._server_dir)
        await io.delete_file(package)
        version = await shellutil.run_executable(self._java_exe, '-jar', self._server_jar, '--version')
        assert version
        logger.log(f'INSTALLED {version}')

    async def _download_url(self, url: str, path: str):
        connector = aiohttp.TCPConnector(family=socket.AF_INET)  # force IPv4
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                                 ' AppleWebKit/537.36 (KHTML, like Gecko)'
                                 ' Chrome/120.0.0.0 Safari/537.36'}
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, read_bufsize=io.DEFAULT_CHUNK_SIZE) as response:
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
        tasks.task_fork(self._deployment.install_runtime(util.get('beta', data)), 'hytale.install_runtime()')
        url = util.get('baseurl', data, '') + subscription_path
        return dict(url=url)


'''
Option                                   Description                            
------                                   -----------                            
--accept-early-plugins                   You acknowledge that loading early     
                                           plugins is unsupported and may cause 
                                           stability issues.                    
--allow-op                                                                      
--assets <Path>                          Asset directory (default: ..           
                                           /HytaleAssets)                       
--auth-mode                              Authentication mode (default:          
  <authenticated|offline|insecure>         AUTHENTICATED)                       
-b, --bind <InetSocketAddress>           Port to listen on (default: 0.0.0.0/0. 
                                           0.0.0:5520)                          
--backup                                                                        
--backup-dir <Path>                                                             
--backup-frequency <Integer>             (default: 30)                          
--backup-max-count <Integer>             (default: 5)                           
--bare                                   Runs the server bare. For example      
                                           without loading worlds, binding to   
                                           ports or creating directories.       
                                           (Note: Plugins will still be loaded  
                                           which may not respect this flag)     
--boot-command <String>                  Runs command on boot. If multiple      
                                           commands are provided they are       
                                           executed synchronously in order.     
--client-pid <Integer>                                                          
--disable-asset-compare                                                         
--disable-cpb-build                      Disables building of compact prefab    
                                           buffers                              
--disable-file-watcher                                                          
--disable-sentry                                                                
--early-plugins <Path>                   Additional early plugin directories to 
                                           load from                            
--event-debug                                                                   
--force-network-flush <Boolean>          (default: true)                        
--generate-schema                        Causes the server generate schema,     
                                           save it into the assets directory    
                                           and then exit                        
--help                                   Print's this message.                  
--identity-token <String>                Identity token (JWT)                   
--log <KeyValueHolder>                   Sets the logger level.                 
--migrate-worlds <String>                Worlds to migrate                      
--migrations <Object2ObjectOpenHashMap>  The migrations to run                  
--mods <Path>                            Additional mods directories            
--owner-name <String>                                                           
--owner-uuid <UUID>                                                             
--prefab-cache <Path>                    Prefab cache directory for immutable   
                                           assets                               
--session-token <String>                 Session token for Session Service API  
--shutdown-after-validate                Automatically shutdown the server      
                                           after asset and/or prefab validation.
--singleplayer                                                                  
-t, --transport <TransportType>          Transport type (default: QUIC)         
--universe <Path>                                                               
--validate-assets                        Causes the server to exit with an      
                                           error code if any assets are invalid.
--validate-prefabs [ValidationOption]    Causes the server to exit with an      
                                           error code if any prefabs are        
                                           invalid.                             
--validate-world-gen                     Causes the server to exit with an      
                                           error code if default world gen is   
                                           invalid.                             
--version                                Prints version information.            
--world-gen <Path>                       World gen directory     
'''
