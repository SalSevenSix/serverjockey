import aiohttp
# ALLOW core.* factorio.messaging
from core.util import util, tasks, io, pack, aggtrf
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.proc import proch, jobh
from core.common import interceptors, rconsvc
from servers.factorio import messaging as msg


class Deployment:

    @staticmethod
    def _default_cmdargs_settings():
        return {
            '_comment_port': 'Port for the Factorio server to use. Default 34197 used if null.',
            'port': None,
            '_comment_rcon-port': 'Optional RCON port.',
            'rcon-port': None,
            '_comment_rcon-password': 'RCON password. Required if RCON port specified.',
            'rcon-password': None,
            '_comment_use-server-whitelist': 'If the whitelist should be used.',
            'use-server-whitelist': False,
            '_comment_use-authserver-bans': 'Verify that connecting players are not banned from multiplayer'
                                            ' and inform Factorio.com about ban/unban commands.',
            'use-authserver-bans': False
        }

    @staticmethod
    def _default_mods_list():
        return {'mods': [{'name': 'base', 'enabled': True}]}

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._runtime_metafile = self._runtime_dir + '/data/changelog.txt'
        self._executable = self._runtime_dir + '/bin/x64/factorio'
        self._current_log = self._runtime_dir + '/factorio-current.log'
        self._autosave_dir = self._runtime_dir + '/saves'
        self._mods_dir = self._runtime_dir + '/mods'
        self._server_settings_def = self._runtime_dir + '/data/server-settings.example.json'
        self._map_settings_def = self._runtime_dir + '/data/map-settings.example.json'
        self._map_gen_settings_def = self._runtime_dir + '/data/map-gen-settings.example.json'
        self._world_dir = self._home_dir + '/world'
        self._save_dir = self._world_dir + '/saves'
        self._map_file = self._save_dir + '/map.zip'
        self._config_dir = self._world_dir + '/config'
        self._cmdargs_settings = self._config_dir + '/cmdargs-settings.json'
        self._server_settings = self._config_dir + '/server-settings.json'
        self._map_settings = self._config_dir + '/map-settings.json'
        self._map_gen_settings = self._config_dir + '/map-gen-settings.json'
        self._server_whitelist = self._config_dir + '/server-whitelist.json'
        self._server_banlist = self._config_dir + '/server-banlist.json'
        self._server_adminlist = self._config_dir + '/server-adminlist.json'
        self._mods_list = self._config_dir + '/mod-list.json'

    async def initialise(self):
        await self.build_world()
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE), self.build_world))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.put('log', httpext.FileSystemHandler(self._current_log))
        r.psh('logs', httpext.FileSystemHandler(self._runtime_dir, ls_filter=_logfiles))
        r.put('*{path}', httpext.FileSystemHandler(self._runtime_dir, 'path'))
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_settings))
        r.put('server', httpext.FileSystemHandler(self._server_settings))
        r.put('map', httpext.FileSystemHandler(self._map_settings))
        r.put('mapgen', httpext.FileSystemHandler(self._map_gen_settings))
        r.put('modslist', httpext.FileSystemHandler(self._mods_list))
        r.put('adminlist', httpext.FileSystemHandler(self._server_adminlist))
        r.put('whitelist', httpext.FileSystemHandler(self._server_whitelist))
        r.put('banlist', httpext.FileSystemHandler(self._server_banlist))
        r.pop()
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile))
        r.put('install-runtime', _InstallRuntimeHandler(self, self._mailer), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-config', httpext.WipeHandler(self._mailer, self._config_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._save_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        cmdargs = util.json_to_dict(await io.read_file(self._cmdargs_settings))
        server = proch.ServerProcess(self._mailer, self._executable)
        port = util.get('port', cmdargs)
        if port:
            server.append_arg('--port').append_arg(port)
        port = port if port else 34197
        rcon_port = util.get('rcon-port', cmdargs)
        rcon_port = rcon_port if rcon_port else port + 1
        server.append_arg('--rcon-port').append_arg(rcon_port)
        rcon_password = util.get('rcon-password', cmdargs)
        rcon_password = rcon_password if rcon_password else util.generate_token(10)
        server.append_arg('--rcon-password').append_arg(rcon_password)
        rconsvc.RconService.set_config(self._mailer, self, rcon_port, rcon_password)
        if cmdargs['use-authserver-bans']:
            server.append_arg('--use-authserver-bans')
        if cmdargs['use-server-whitelist']:
            server.append_arg('--use-server-whitelist')
            server.append_arg('--server-whitelist').append_arg(self._server_whitelist)
        server.append_arg('--server-banlist').append_arg(self._server_banlist)
        server.append_arg('--server-adminlist').append_arg(self._server_adminlist)
        server.append_arg('--server-settings').append_arg(self._server_settings)
        server.append_arg('--start-server').append_arg(self._map_file)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._config_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        await io.create_directory(self._mods_dir)
        if not await io.file_exists(self._server_settings):
            await io.copy_text_file(self._server_settings_def, self._server_settings)
        if not await io.file_exists(self._map_settings):
            await io.copy_text_file(self._map_settings_def, self._map_settings)
        if not await io.file_exists(self._map_gen_settings):
            await io.copy_text_file(self._map_gen_settings_def, self._map_gen_settings)
        if not await io.file_exists(self._server_whitelist):
            await io.write_file(self._server_whitelist, '[]')
        if not await io.file_exists(self._server_banlist):
            await io.write_file(self._server_banlist, '[]')
        if not await io.file_exists(self._server_adminlist):
            await io.write_file(self._server_adminlist, '[]')
        if not await io.file_exists(self._cmdargs_settings):
            await io.write_file(
                self._cmdargs_settings, util.obj_to_json(Deployment._default_cmdargs_settings(), pretty=True))
        if not await io.file_exists(self._mods_list):
            await io.write_file(
                self._mods_list, util.obj_to_json(Deployment._default_mods_list(), pretty=True))

    async def install_runtime(self, version: str):
        url = 'https://factorio.com/get-download/' + version + '/headless/linux64'
        install_package = self._home_dir + '/factorio.tar.xz'
        unpack_dir = self._home_dir + '/factorio'
        chunk_size = 65536
        try:
            self._mailer.post(self, msg.INSTALL_START)
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'START Install')
            await io.delete_file(install_package)
            await io.delete_directory(unpack_dir)
            await io.delete_directory(self._runtime_dir)
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'DOWNLOADING ' + url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, read_bufsize=chunk_size) as response:
                    assert response.status == 200
                    tracker = None
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        tracker = _DownloadTracker(self._mailer, msg.DEPLOYMENT_MSG, int(content_length), 10)
                    await io.stream_write_file(install_package, io.WrapReader(response.content), chunk_size, tracker)
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'UNPACKING ' + install_package)
            await pack.unpack_tarxz(install_package, self._home_dir)
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'INSTALLING Factorio server')
            await io.rename_path(unpack_dir, self._runtime_dir)
            await io.delete_file(install_package)
            await self.build_world()
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'END Install')
        except Exception as e:
            self._mailer.post(self, msg.DEPLOYMENT_MSG, repr(e))
        finally:
            self._mailer.post(self, msg.INSTALL_DONE)

    async def ensure_map(self):
        if not await io.file_exists(self._map_file):
            await io.delete_directory(self._save_dir)
            await io.create_directory(self._save_dir)
            await jobh.JobProcess.run_job(self._mailer, self, (
                self._executable,
                '--create', self._map_file,
                '--map-gen-settings', self._map_gen_settings,
                '--map-settings', self._map_settings))
        if not await io.symlink_exists(self._autosave_dir):
            await io.create_symlink(self._autosave_dir, self._save_dir)

    async def sync_mods(self):
        mods = util.json_to_dict(await io.read_file(self._mods_list))
        settings = util.json_to_dict(await io.read_file(self._server_settings))
        if not settings.get('username') or not settings.get('token'):
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'Unable to sync mods, credentials unavailable')
            return
        self._mailer.post(self, msg.DEPLOYMENT_MSG, 'Syncing mods...')
        baseurl, mod_files, mod_list, chunk_size = 'https://mods.factorio.com', [], [], 65536
        credentials = '?username=' + settings['username'] + '&token=' + settings['token']
        async with aiohttp.ClientSession() as session:
            for mod in mods['mods']:
                mod_list.append({'name': mod['name'], 'enabled': mod['enabled']})
                if mod['name'] != 'base':
                    mod_meta_url = baseurl + '/api/mods/' + mod['name']
                    async with session.get(mod_meta_url) as meta_response:
                        assert meta_response.status == 200
                        meta = await meta_response.json()
                        if not mod.get('version'):
                            mod['version'] = meta['releases'][-1]['version']
                    mod_version_found = False
                    for release in meta['releases']:
                        if release['version'] == mod['version']:
                            mod_version_found = True
                            mod_files.append(release['file_name'])
                            filename = self._mods_dir + '/' + release['file_name']
                            if not await io.file_exists(filename):
                                self._mailer.post(self, msg.DEPLOYMENT_MSG, 'Downloading ' + release['file_name'])
                                filename_part = filename + '.part'  # TODO this is now redundant
                                await io.delete_file(filename_part)
                                download_url = baseurl + release['download_url'] + credentials
                                async with session.get(download_url, read_bufsize=chunk_size) as modfile_response:
                                    assert modfile_response.status == 200
                                    await io.stream_write_file(
                                        filename_part, io.WrapReader(modfile_response.content), chunk_size)
                                await io.rename_path(filename_part, filename)
                    if not mod_version_found:
                        self._mailer.post(self, msg.DEPLOYMENT_MSG, 'ERROR: Mod ' + mod['name'] + ' version '
                                          + mod['version'] + ' not found, see ' + mod_meta_url)
        for file in await io.directory_list(self._mods_dir):
            if file['type'] == 'file' and file['name'].endswith('.zip') and file['name'] not in mod_files:
                await io.delete_file(self._mods_dir + '/' + file['name'])
        await io.write_file(self._mods_dir + '/mod-list.json', util.obj_to_json({'mods': mod_list}))


class _InstallRuntimeHandler(httpabc.PostHandler):

    def __init__(self, deployment: Deployment, mailer: msgabc.MulticastMailer):
        self._mailer = mailer
        self._deployment = deployment

    async def handle_post(self, resource, data):
        subscription_path = await httpsubs.HttpSubscriptionService.subscribe(
            self._mailer, self, httpsubs.Selector(
                msg_filter=msg.FILTER_DEPLOYMENT_MSG,
                completed_filter=msg.FILTER_INSTALL_DONE,
                aggregator=aggtrf.StrJoin('\n')))
        version = util.get('beta', data, 'stable')
        tasks.task_fork(self._deployment.install_runtime(version), 'factorio.install_runtime()')
        return {'url': util.get('baseurl', data, '') + subscription_path}


class _DownloadTracker(io.BytesTracker):

    def __init__(self, mailer: msgabc.MulticastMailer, msg_name: str, expected: int, notifications: int):
        self._mailer = mailer
        self._msg_name = msg_name
        self._expected = expected
        self._progress = 0
        self._increment = int(expected / notifications)
        self._next_target = self._increment

    def processed(self, chunk: bytes):
        self._progress += len(chunk)
        if self._progress >= self._expected:
            self._mailer.post(self, self._msg_name, 'downloaded 100%')
        elif self._progress > self._next_target:
            self._next_target += self._increment
            message = 'downloaded  ' + str(int((self._progress / self._expected) * 100.0)) + '%'
            self._mailer.post(self, self._msg_name, message)


def _logfiles(entry) -> bool:
    return entry['type'] == 'file' and entry['name'].endswith('.log')
