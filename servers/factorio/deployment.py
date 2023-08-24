import aiohttp
import socket
# ALLOW core.* factorio.messaging
from core.util import util, tasks, io, pack, aggtrf, funcutil, objconv
from core.msg import msgabc, msgext, msgftr, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.system import svrsvc
from core.proc import proch, jobh
from core.common import interceptors, rconsvc, portmapper
from servers.factorio import messaging as msg

_MAP, _ZIP = 'map', '.zip'
_AUTOSAVE_PREFIX = '_autosave'


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
        'use-authserver-bans': False,
        '_comment_server-upnp': 'Try to automatically redirect server port on home network using UPnP.',
        'server-upnp': True,
        '_comment_rcon-upnp': 'Try to automatically redirect rcon port on home network using UPnP.',
        'rcon-upnp': False
    }


def _default_mods_list():
    return {'mods': [{'name': 'base', 'enabled': True}]}


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir, self._tmp_dir = context.config('home'), context.config('tmpdir')
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
        self._map_file = self._save_dir + '/' + _MAP + _ZIP
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
        self._mailer.register(portmapper.PortMapperService(self._mailer))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE), self.build_world))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer, self._tmp_dir), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer, self._tmp_dir), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.put('log', httpext.FileSystemHandler(self._current_log))
        r.psh('logs', httpext.FileSystemHandler(self._runtime_dir, ls_filter=_logfiles))
        r.put('*{path}', httpext.FileSystemHandler(self._runtime_dir, 'path'), 'r')
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_settings), 'm')
        r.put('server', httpext.FileSystemHandler(self._server_settings), 'm')
        r.put('map', httpext.FileSystemHandler(self._map_settings), 'm')
        r.put('mapgen', httpext.FileSystemHandler(self._map_gen_settings), 'm')
        r.put('modslist', httpext.FileSystemHandler(self._mods_list), 'm')
        r.put('adminlist', httpext.FileSystemHandler(self._server_adminlist), 'm')
        r.put('whitelist', httpext.FileSystemHandler(self._server_whitelist), 'm')
        r.put('banlist', httpext.FileSystemHandler(self._server_banlist), 'm')
        r.pop()
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile))
        r.put('install-runtime', _InstallRuntimeHandler(self, self._mailer), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-config', httpext.WipeHandler(self._mailer, self._config_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._map_file), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.put('restore-autosave', _RestoreAutosaveHandler(self), 'r')
        r.pop()
        r.psh('autosaves', httpext.FileSystemHandler(self._save_dir, ls_filter=_autosaves))
        r.put('*{path}', httpext.FileSystemHandler(self._save_dir, 'path'), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tmp_dir=self._tmp_dir,
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('Factorio game server not installed. Please Install Runtime first.')
        svrsvc.ServerStatus.notify_state(self._mailer, self, 'START')  # Pushing early because slow pre-start tasks
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_settings))
        await self._sync_mods()
        await self._ensure_map()
        server = proch.ServerProcess(self._mailer, self._executable)
        port = util.get('port', cmdargs)
        if port:
            server.append_arg('--port').append_arg(port)
        port = port if port else 34197
        if util.get('server-upnp', cmdargs, True):
            portmapper.map_port(self._mailer, self, port, portmapper.UDP, 'Factorio server')
        rcon_port = util.get('rcon-port', cmdargs)
        rcon_port = rcon_port if rcon_port else port + 1
        server.append_arg('--rcon-port').append_arg(rcon_port)
        rcon_password = util.get('rcon-password', cmdargs)
        rcon_password = rcon_password if rcon_password else util.generate_token(10)
        server.append_arg('--rcon-password').append_arg(rcon_password)
        rconsvc.RconService.set_config(self._mailer, self, rcon_port, rcon_password)
        if util.get('rcon-upnp', cmdargs, False):
            portmapper.map_port(self._mailer, self, rcon_port, portmapper.TCP, 'Factorio rcon')
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
            await io.write_file(self._cmdargs_settings, objconv.obj_to_json(_default_cmdargs_settings(), pretty=True))
        if not await io.file_exists(self._mods_list):
            await io.write_file(self._mods_list, objconv.obj_to_json(_default_mods_list(), pretty=True))

    async def install_runtime(self, version: str):
        url = 'https://factorio.com/get-download/' + version + '/headless/linux64'
        install_package = self._home_dir + '/factorio.tar.xz'
        unpack_dir = self._home_dir + '/factorio'
        chunk_size = io.DEFAULT_CHUNK_SIZE
        try:
            self._mailer.post(self, msg.DEPLOYMENT_START)
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'START Install')
            await io.delete_file(install_package)
            await io.delete_directory(unpack_dir)
            await io.delete_directory(self._runtime_dir)
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'DOWNLOADING ' + url)
            connector = aiohttp.TCPConnector(family=socket.AF_INET)  # Force IPv4
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, read_bufsize=chunk_size) as response:
                    assert response.status == 200
                    tracker, content_length = None, response.headers.get('Content-Length')
                    if content_length:
                        tracker = msglog.PercentTracker(self._mailer, int(content_length), prefix='downloaded')
                    await io.stream_write_file(
                        install_package, io.WrapReader(response.content), chunk_size, self._tmp_dir, tracker)
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
            self._mailer.post(self, msg.DEPLOYMENT_DONE)

    async def _ensure_map(self):
        if not await io.file_exists(self._map_file):
            await jobh.JobProcess.run_job(self._mailer, self, (
                self._executable,
                '--create', self._map_file,
                '--map-gen-settings', self._map_gen_settings,
                '--map-settings', self._map_settings))
        if not await io.symlink_exists(self._autosave_dir):
            await io.create_symlink(self._autosave_dir, self._save_dir)

    async def _sync_mods(self):
        mods = objconv.json_to_dict(await io.read_file(self._mods_list))
        if not util.get('mods', mods):
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'Mod sync disabled')
            return
        settings = objconv.json_to_dict(await io.read_file(self._server_settings))
        if not settings.get('username') or not settings.get('token'):
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'Unable to sync mods, credentials unavailable')
            return
        self._mailer.post(self, msg.DEPLOYMENT_MSG, 'SYNCING mods...')
        baseurl, mod_files, mod_list, chunk_size = 'https://mods.factorio.com', [], [], io.DEFAULT_CHUNK_SIZE
        connector = aiohttp.TCPConnector(family=socket.AF_INET)  # Force IPv4
        timeout = aiohttp.ClientTimeout(total=8.0)
        credentials = '?username=' + settings['username'] + '&token=' + settings['token']
        async with aiohttp.ClientSession(connector=connector) as session:
            for mod in mods['mods']:
                mod_list.append({'name': mod['name'], 'enabled': mod['enabled']})
                if mod['name'] != 'base':
                    mod_meta_url = baseurl + '/api/mods/' + mod['name']
                    async with session.get(mod_meta_url, timeout=timeout) as meta_response:
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
                                self._mailer.post(self, msg.DEPLOYMENT_MSG, 'DOWNLOADING ' + release['file_name'])
                                download_url = baseurl + release['download_url'] + credentials
                                async with session.get(download_url, read_bufsize=chunk_size) as modfile_response:
                                    assert modfile_response.status == 200
                                    tracker, content_length = None, modfile_response.headers.get('Content-Length')
                                    if content_length:
                                        tracker = msglog.PercentTracker(
                                            self._mailer, int(content_length), notifications=5, prefix='downloaded')
                                    await io.stream_write_file(
                                        filename, io.WrapReader(modfile_response.content),
                                        chunk_size, self._tmp_dir, tracker)
                    if not mod_version_found:
                        self._mailer.post(self, msg.DEPLOYMENT_MSG, 'ERROR Mod ' + mod['name'] + ' version '
                                          + mod['version'] + ' not found, see ' + mod_meta_url)
        for file in await io.directory_list(self._mods_dir):
            if file['type'] == 'file' and file['name'].endswith(_ZIP) and file['name'] not in mod_files:
                await io.delete_file(self._mods_dir + '/' + file['name'])
        await io.write_file(self._mods_dir + '/mod-list.json', objconv.obj_to_json({'mods': mod_list}))

    async def restore_autosave(self, filename: str):
        map_backup = self._save_dir + '/' + _AUTOSAVE_PREFIX + '_' + _MAP + '_backup' + _ZIP
        try:
            self._mailer.post(self, msg.DEPLOYMENT_START)
            filename = filename[1:] if filename[0] == '/' else filename
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'RESTORING ' + filename)
            autosave_file = self._save_dir + '/' + filename
            if not await io.file_exists(autosave_file):
                raise FileNotFoundError(autosave_file)
            autosave_size = await io.file_size(autosave_file)
            tracker = msglog.PercentTracker(self._mailer, autosave_size, notifications=4)
            if await io.file_exists(self._map_file):
                if map_backup == autosave_file:
                    await io.delete_file(self._map_file)
                else:
                    await io.delete_file(map_backup)
                    await io.rename_path(self._map_file, map_backup)
            await io.stream_copy_file(autosave_file, self._map_file, io.DEFAULT_CHUNK_SIZE * 2, self._tmp_dir, tracker)
            self._mailer.post(self, msg.DEPLOYMENT_MSG, 'Autosave ' + filename + ' restored')
            await funcutil.silently_call(io.delete_file(map_backup))
        except Exception as e:
            self._mailer.post(self, msg.DEPLOYMENT_MSG, repr(e))
        finally:
            self._mailer.post(self, msg.DEPLOYMENT_DONE)


class _InstallRuntimeHandler(httpabc.PostHandler):

    def __init__(self, deployment: Deployment, mailer: msgabc.MulticastMailer):
        self._mailer = mailer
        self._deployment = deployment

    async def handle_post(self, resource, data):
        subscription_path = await httpsubs.HttpSubscriptionService.subscribe(
            self._mailer, self, httpsubs.Selector(
                msg_filter=msg.FILTER_DEPLOYMENT_MSG,
                completed_filter=msg.FILTER_DEPLOYMENT_DONE,
                aggregator=aggtrf.StrJoin('\n')))
        version = util.get('beta', data, 'stable')
        tasks.task_fork(self._deployment.install_runtime(version), 'factorio.install_runtime()')
        return {'url': util.get('baseurl', data, '') + subscription_path}


class _RestoreAutosaveHandler(httpabc.PostHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    def handle_post(self, resource, data):
        filename = util.get('filename', data)
        if not filename or filename.endswith(_MAP + _ZIP):
            return httpabc.ResponseBody.BAD_REQUEST
        tasks.task_fork(self._deployment.restore_autosave(filename), 'factorio.restore_autosave()')
        return httpabc.ResponseBody.NO_CONTENT


def _logfiles(entry) -> bool:
    return entry['type'] == 'file' and entry['name'].endswith('.log')


def _autosaves(entry) -> bool:
    return entry['type'] == 'file' and entry['name'].startswith(_AUTOSAVE_PREFIX) and entry['name'].endswith(_ZIP)
