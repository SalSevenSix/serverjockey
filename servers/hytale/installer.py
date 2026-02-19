import socket
import asyncio
import aiohttp
# ALLOW core.*
from core.util import util, io, pack, shellutil, funcutil, objconv, linenc
from core.msg import msglog, msgpipe
from core.context import contextsvc

_LAUNCHER_EXE = 'hytale-downloader-linux-amd64'


class Installer:

    def __init__(self, context: contextsvc.Context, logger: msglog.LogPublisher, tempdir: str,
                 runtime_dir: str, runtime_meta: str, server_dir: str, server_jar: str, java_dir: str, java_exe: str):
        self._context, self._logger, self._tempdir = context, logger, tempdir
        self._runtime_dir, self._runtime_meta = runtime_dir, runtime_meta
        self._server_dir, self._server_jar = server_dir, server_jar
        self._java_dir, self._java_exe = java_dir, java_exe
        self._launcher_exe = runtime_dir + '/' + _LAUNCHER_EXE

    async def install_runtime(self, version: str):
        meta = {}
        if await io.file_exists(self._runtime_meta):
            meta = objconv.json_to_dict(await io.read_file(self._runtime_meta))
            await io.delete_file(self._runtime_meta)
        else:
            await io.delete_directory(self._runtime_dir)
            await io.create_directory(self._runtime_dir)
            meta['java'] = await self._install_java()
            meta['launcher'] = await self._install_launcher()
        server_package = await self._download_server(version)
        meta['server'] = await self._install_server(server_package)
        await io.write_file(self._runtime_meta, objconv.obj_to_json(meta, True))

    async def _install_java(self) -> str:
        url = 'https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk'
        self._logger.log(f'DOWNLOADING Java ({url})')
        package = self._runtime_dir + '/java.tar.gz'
        await self._download_url(url, package)
        self._logger.log('UNPACKING Java')
        await pack.unpack_targz(package, self._runtime_dir)
        unpacked = await io.directory_list(self._runtime_dir)
        unpacked = util.single([e['name'] for e in unpacked if e['name'].startswith('jdk')])
        assert unpacked
        await io.rename_path(self._runtime_dir + '/' + unpacked, self._java_dir)
        await io.delete_file(package)
        version = await shellutil.run_executable(self._java_exe, '--version')
        assert version
        self._logger.log('INSTALLED Java (' + util.single(version.split('\n')) + ')')
        return version

    async def _install_launcher(self) -> str:
        url = 'https://downloader.hytale.com/hytale-downloader.zip'
        self._logger.log(f'DOWNLOADING HytaleLauncher ({url})')
        package = self._runtime_dir + '/launcher.zip'
        await self._download_url(url, package)
        self._logger.log('UNPACKING HytaleLauncher')
        unpacked = self._runtime_dir + '/launcher'
        await io.create_directory(unpacked)
        await pack.unpack_archive(package, unpacked)
        await io.move_path(unpacked + '/' + _LAUNCHER_EXE, self._launcher_exe)
        await io.chmod(self._launcher_exe, 0o744)
        await io.delete_directory(unpacked)
        await io.delete_file(package)
        version = await shellutil.run_executable(self._launcher_exe, '-version')
        assert version
        self._logger.log(f'INSTALLED HytaleLauncher ({version})')
        return version

    async def _download_server(self, version: str) -> str:
        self._logger.log('DOWNLOADING HytaleServer (' + (version.strip() if version else 'release') + ')')
        stderr, stdout, package = None, None, self._server_dir + '.zip'
        await io.delete_file(package)
        args = ['-download-path', package]
        if version:
            args.append('-patchline')
            args.append(version.strip())
        try:
            self._logger.log('RUNNING ' + _LAUNCHER_EXE + ' ' + ' '.join(args))
            mailer, source, name, = self._logger.mailer(), self._logger.source(), self._logger.name()
            decoder = linenc.PtyLineDecoder()
            process = await asyncio.create_subprocess_exec(
                self._launcher_exe, *args, env=self._context.env(), cwd=self._runtime_dir,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stderr = msgpipe.PipeOutLineProducer(mailer, source, name, process.stderr, decoder)
            stdout = msgpipe.PipeOutLineProducer(mailer, source, name, process.stdout, decoder)
            rc = await process.wait()
            if rc != 0:
                raise Exception(f'HytaleServer download failed (exit code {rc})')
            self._logger.log('DOWNLOADED HytaleServer')
            return package
        finally:
            await funcutil.silently_cleanup(stdout)
            await funcutil.silently_cleanup(stderr)

    async def _install_server(self, package: str) -> str:
        self._logger.log('UNPACKING HytaleServer')
        await io.delete_directory(self._server_dir)
        await io.create_directory(self._server_dir)
        await pack.unpack_archive(package, self._server_dir)
        await io.delete_file(package)
        version = await shellutil.run_executable(self._java_exe, '-jar', self._server_jar, '--version')
        assert version
        self._logger.log(f'INSTALLED {version}')
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
