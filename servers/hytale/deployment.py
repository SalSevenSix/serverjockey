import socket
import asyncio
import aiohttp
# ALLOW core.* hytale.messaging
from core.util import gc, util, tasks, io, aggtrf, pack, shellutil, funcutil, objconv, linenc
from core.msg import msgabc, msglog, msgpipe
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.proc import proch
from core.common import svrhelpers, portmapper
from servers.hytale import messaging as msg

LAUNCHER_EXE = 'hytale-downloader-linux-amd64'
MOD_EXTS = 'jar', 'zip'


def _default_cmdargs() -> dict:
    return {
        '_comment_accept-early-plugins': 'Allow loading early plugins, may cause stability issues',
        '--accept-early-plugins': False,
        '_comment_allow-op': 'Allow use of /op console command',
        '--allow-op': False,
        '_comment_auth-mode': 'Authentication mode, values: authenticated|offline|insecure default: authenticated',
        '--auth-mode': None,
        '_comment_bind': 'Port to listen on, default: 0.0.0.0/0.0.0.0:5520',
        '--bind': None,
        '_comment_backup': 'Enable automated backups',
        '--backup': False,
        '_comment_backup-frequency': 'Backup frequency as integer, default: 30',
        '--backup-frequency': None,
        '_comment_backup-max-count': 'Backup count as integer, default: 5',
        '--backup-max-count': None,
        '_comment_bare': 'Runs the server bare',
        '--bare': False,
        '_comment_boot-command': 'Runs command on boot, multiple allowed',
        '--boot-command': None,
        '_comment_client-pid': 'Client PID, integer',
        '--client-pid': None,
        '_comment_disable-asset-compare': 'Disable asset compare',
        '--disable-asset-compare': False,
        '_comment_disable-cpb-build': 'Disables building of compact prefab buffers',
        '--disable-cpb-build': False,
        '_comment_disable-file-watcher': 'Disable file watcher',
        '--disable-file-watcher': False,
        '_comment_disable-sentry': 'Disable sentry',
        '--disable-sentry': False,
        '_comment_event-debug': 'Event debug',
        '--event-debug': False,
        '_comment_force-network-flush': 'Force network flush, default: true',
        '--force-network-flush': None,
        '_comment_identity-token': 'Identity token (JWT)',
        '--identity-token': None,
        '_comment_log': 'Set the logger level',
        '--log': None,
        '_comment_owner-name': 'Owner name',
        '--owner-name': None,
        '_comment_owner-uuid': 'Owner UUID',
        '--owner-uuid': None,
        '_comment_session-token': 'Session token for Session Service API',
        '--session-token': None,
        '_comment_singleplayer': 'Singleplayer mode',
        '--singleplayer': False,
        '_comment_transport': 'Transport type, default: QUIC',
        '--transport': None,
        '_comment_server_upnp': 'Try to automatically redirect server port on home network using UPnP',
        'server_upnp': True
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._runtime_meta = self._runtime_dir + '/versions.text'
        self._launcher_exe = self._runtime_dir + '/' + LAUNCHER_EXE
        self._java_dir = self._runtime_dir + '/java'
        self._java_exe = self._java_dir + '/bin/java'
        self._server_dir = self._runtime_dir + '/server'
        self._server_jar = self._server_dir + '/Server/HytaleServer.jar'
        self._world_dir = self._home_dir + '/world'
        self._autobackups_dir = self._world_dir + '/backups'
        self._logs_dir = self._world_dir + '/logs'
        self._mods_dir = self._world_dir + '/mods'
        self._save_dir = self._world_dir + '/universe'
        self._map_dir = self._save_dir + '/worlds/default'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_ports().init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta_runtime(self._runtime_meta)
        builder.put_meta_world(httpext.MtimeHandler().check(self._map_dir + '/resources').dir(self._logs_dir))
        builder.put_installer(_InstallRuntimeHandler(self, self._context))
        builder.put_wipes(self._runtime_dir, dict(
            all=self._world_dir, logs=self._logs_dir, autobackups=self._autobackups_dir,
            save=dict(path=self._map_dir, ls_filter=_ls_mapdata)))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.put('restore-autobackup', httpext.UnpackerHandler(
            self._context, self._autobackups_dir, self._save_dir, to_root=True), 'r')
        builder.pop()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.psh('autobackups', httpext.FileSystemHandler(self._autobackups_dir, ls_filter=_ls_autobackups))
        builder.put('*{path}', httpext.FileSystemHandler(self._autobackups_dir, 'path', ls_filter=_ls_autobackups), 'r')
        builder.pop()
        builder.put_config(dict(
            cmdargs=self._cmdargs_file, config=self._world_dir + '/config.json',
            permissions=self._world_dir + '/permissions.json', bans=self._world_dir + '/bans.json',
            whitelist=self._world_dir + '/whitelist.json', default=self._map_dir + '/config.json'))
        builder.psh('modfiles', httpext.FileSystemHandler(self._mods_dir, ls_filter=_ls_modfile))
        builder.put('*{path}', httpext.FileSystemHandler(self._mods_dir, 'path', tempdir=self._tempdir), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._server_jar):
            raise FileNotFoundError('Hytale game server not installed. Please Install Runtime first.')
        cmdargs, jreargs, svrargs = await self._load_args()
        self._map_ports(cmdargs)
        server = proch.ServerProcess(self._context, self._java_exe)
        server.use_cwd(self._world_dir).use_out_decoder(linenc.PtyLineDecoder())
        server.append_arg('-XX:AOTCache=' + self._server_dir + '/Server/HytaleServer.aot')
        server.append_struct(jreargs)
        server.append_arg('-jar').append_arg(self._server_jar)
        server.append_arg('--assets').append_arg(self._server_dir + '/Assets.zip')
        server.append_arg('--universe').append_arg(self._save_dir)
        server.append_arg('--backup-dir').append_arg(self._world_dir + '/backups')
        server.append_struct(svrargs)
        return server

    async def build_world(self):
        await io.create_directory(
            self._backups_dir, self._world_dir, self._logs_dir, self._mods_dir, self._autobackups_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        await io.keyfill_json_file(self._cmdargs_file, _default_cmdargs())

    async def _load_args(self) -> tuple:
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        jreargs, svrargs, cmdargs = {}, {}, util.delete_dict(cmdargs, (
            '-b', '-t', '-jar', '--version', '--help', '--assets', '--universe', '--world-gen', '--backup-dir',
            '--early-plugins', '--generate-schema', '--migrate-worlds', '--migrations', '--mods', '--prefab-cache',
            '--shutdown-after-validate', '--validate-assets', '--validate-prefabs', '--validate-world-gen'))
        for key, value in cmdargs.items():
            if key and key.startswith('--'):
                svrargs[key] = value
            elif key and key.startswith('-') and not key.startswith('-XX:AOTCache'):
                jreargs[key] = value
        return cmdargs, jreargs, svrargs

    def _map_ports(self, cmdargs: dict):
        if not util.get('server_upnp', cmdargs, True):
            return
        port = util.get('--bind', cmdargs)
        if not port:
            port = 5520
        if isinstance(port, str):
            port = int(util.lchop(util.lchop(port, '/'), ':'))
        portmapper.map_port(self._context, self, port, gc.UDP, 'Hytale Server port')

    async def install_runtime(self, version: str):
        logger = msglog.LogPublisher(self._context, self)
        try:
            self._context.post(self, msg.DEPLOYMENT_START)
            logger.log('START Install')
            await io.delete_directory(self._runtime_dir)
            await io.create_directory(self._runtime_dir)
            meta = '=== JAVA ===\n' + await self._install_java(logger)
            meta += '\n\n=== LAUNCHER ===\n' + await self._install_launcher(logger)
            server_package = await self._download_server(logger, version)
            meta += '\n\n=== SERVER ===\n' + await self._install_server(logger, server_package)
            await io.write_file(self._runtime_meta, meta)
            await self.build_world()
            logger.log('END Install')
        except Exception as e:
            logger.log(repr(e))
        finally:
            self._context.post(self, msg.DEPLOYMENT_DONE)

    async def _install_java(self, logger) -> str:
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
        logger.log('INSTALLED Java (' + util.single(version.split('\n')) + ')')
        return version

    async def _install_launcher(self, logger) -> str:
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
        return version

    async def _download_server(self, logger, version: str) -> str:
        logger.log('DOWNLOADING HytaleServer (' + (version.strip() if version else 'release') + ')')
        stderr, stdout, package = None, None, self._server_dir + '.zip'
        args = ['-download-path', package]
        if version:
            args.append('-patchline')
            args.append(version.strip())
        try:
            logger.log('RUNNING ' + LAUNCHER_EXE + ' ' + ' '.join(args))
            mailer, source, name, decoder = logger.mailer(), logger.source(), logger.name(), linenc.PtyLineDecoder()
            process = await asyncio.create_subprocess_exec(
                self._launcher_exe, *args, env=self._context.env(), cwd=self._runtime_dir,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stderr = msgpipe.PipeOutLineProducer(mailer, source, name, process.stderr, decoder)
            stdout = msgpipe.PipeOutLineProducer(mailer, source, name, process.stdout, decoder)
            rc = await process.wait()
            if rc != 0:
                raise Exception(f'HytaleServer download failed (exit code {rc})')
            logger.log('DOWNLOADED HytaleServer')
            return package
        finally:
            await funcutil.silently_cleanup(stdout)
            await funcutil.silently_cleanup(stderr)

    async def _install_server(self, logger, package: str) -> str:
        logger.log('UNPACKING HytaleServer')
        await io.create_directory(self._server_dir)
        await pack.unpack_archive(package, self._server_dir)
        await io.delete_file(package)
        version = await shellutil.run_executable(self._java_exe, '-jar', self._server_jar, '--version')
        assert version
        logger.log(f'INSTALLED {version}')
        return version

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


def _ls_mapdata(entry) -> bool:
    return entry['type'] == 'directory'


def _ls_modfile(entry) -> bool:
    ftype, fname, fext = entry['type'], entry['name'], util.fext(entry['name'])
    return ftype == 'file' and fname and len(fname) > 4 and fext in MOD_EXTS


def _ls_autobackups(entry) -> bool:
    return entry['type'] == 'file' and util.fext(entry['name']) == 'zip'
