import socket
import aiohttp
# ALLOW core.* factorio.messaging
from core.util import gc, util, idutil, tasks, io, pack, aggtrf, funcutil, objconv
from core.msg import msgabc, msglog
from core.msgc import sc
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.system import svrsvc
from core.proc import proch, jobh
from core.common import rconsvc, portmapper, svrhelpers
from servers.factorio import messaging as msg

_MAP, _ZIP, _AUTOSAVE_PREFIX = 'map', '.zip', '_autosave'
_BASE_MOD_NAMES = 'base', 'elevated-rails', 'quality', 'space-age'


def _default_cmdargs_settings() -> dict:
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


def _default_mods_list() -> dict:
    mods = []
    for mod in _BASE_MOD_NAMES:
        mods.append(dict(name=mod, enabled=True))
    return dict(mods=mods)


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._executable = self._runtime_dir + '/bin/x64/factorio'
        self._mods_dir = self._runtime_dir + '/mods'
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
        helper = svrhelpers.DeploymentInitHelper(self._context, self.build_world)
        helper.init_ports().init_jobs(no_rebuild=True).init_archiving(self._tempdir).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/data/changelog.txt',
                         httpext.MtimeHandler().check(self._map_file).dir(self._save_dir))
        builder.put_installer(_InstallRuntimeHandler(self, self._context))
        builder.put_wipes(self._runtime_dir, dict(save=self._map_file, config=self._config_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.put('restore-autosave', _RestoreAutosaveHandler(self), 'r')
        builder.pop()
        builder.put_log(self._runtime_dir + '/factorio-current.log').put_logs(self._runtime_dir, ls_filter=_logfiles)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.psh('autosaves', httpext.FileSystemHandler(self._save_dir, ls_filter=_autosaves))
        builder.put('*{path}', httpext.FileSystemHandler(self._save_dir, 'path'), 'r')
        builder.pop()
        builder.put_config(dict(
            cmdargs=self._cmdargs_settings, server=self._server_settings, map=self._map_settings,
            mapgen=self._map_gen_settings, modslist=self._mods_list, adminlist=self._server_adminlist,
            whitelist=self._server_whitelist, banlist=self._server_banlist))

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('Factorio game server not installed. Please Install Runtime first.')
        svrsvc.ServerStatus.notify_state(self._context, self, sc.START)  # pushing early because slow pre-start tasks
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_settings))
        await self._sync_mods()
        await self._ensure_map()
        server = proch.ServerProcess(self._context, self._executable)
        port = util.get('port', cmdargs)
        if port:
            server.append_arg('--port').append_arg(port)
        port = port if port else 34197
        if util.get('server-upnp', cmdargs, True):
            portmapper.map_port(self._context, self, port, gc.UDP, 'Factorio server')
        rcon_port = util.get('rcon-port', cmdargs)
        rcon_port = rcon_port if rcon_port else port + 1
        server.append_arg('--rcon-port').append_arg(rcon_port)
        rcon_password = util.get('rcon-password', cmdargs)
        rcon_password = rcon_password if rcon_password else idutil.generate_token(10)
        server.append_arg('--rcon-password').append_arg(rcon_password)
        rconsvc.RconService.set_config(self._context, self, rcon_port, rcon_password)
        if util.get('rcon-upnp', cmdargs, False):
            portmapper.map_port(self._context, self, rcon_port, gc.TCP, 'Factorio rcon')
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
        await io.create_directory(self._backups_dir, self._world_dir, self._save_dir, self._config_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        await io.create_directory(self._mods_dir)
        if not await io.file_exists(self._server_settings):
            await io.copy_text_file(self._runtime_dir + '/data/server-settings.example.json', self._server_settings)
        if not await io.file_exists(self._map_settings):
            await io.copy_text_file(self._runtime_dir + '/data/map-settings.example.json', self._map_settings)
        if not await io.file_exists(self._map_gen_settings):
            await io.copy_text_file(self._runtime_dir + '/data/map-gen-settings.example.json', self._map_gen_settings)
        if not await io.file_exists(self._server_whitelist):
            await io.write_file(self._server_whitelist, '[]')
        if not await io.file_exists(self._server_banlist):
            await io.write_file(self._server_banlist, '[]')
        if not await io.file_exists(self._server_adminlist):
            await io.write_file(self._server_adminlist, '[]')
        await io.keyfill_json_file(self._cmdargs_settings, _default_cmdargs_settings())
        await io.keyfill_json_file(self._mods_list, _default_mods_list())

    async def install_runtime(self, version: str):
        logger = msglog.LogPublisher(self._context, self)
        url = 'https://factorio.com/get-download/' + version + '/headless/linux64'
        install_package, unpack_dir = self._home_dir + '/factorio.tar.xz', self._home_dir + '/factorio'
        try:
            self._context.post(self, msg.DEPLOYMENT_START)
            logger.log('START Install')
            await io.delete_file(install_package)
            await io.delete_directory(unpack_dir)
            await io.delete_directory(self._runtime_dir)
            logger.log('DOWNLOADING ' + url)
            connector = aiohttp.TCPConnector(family=socket.AF_INET)  # force IPv4
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, read_bufsize=io.DEFAULT_CHUNK_SIZE) as response:
                    assert response.status == 200
                    tracker, content_length = None, response.headers.get('Content-Length')
                    if content_length:
                        tracker = msglog.PercentTracker(self._context, int(content_length), prefix='downloaded')
                    await io.stream_write_file(
                        install_package, io.WrapReader(response.content), io.DEFAULT_CHUNK_SIZE, self._tempdir, tracker)
            logger.log('UNPACKING ' + install_package)
            await pack.unpack_tarxz(install_package, self._home_dir)
            logger.log('INSTALLING Factorio server')
            await io.rename_path(unpack_dir, self._runtime_dir)
            await io.delete_file(install_package)
            await self.build_world()
            logger.log('END Install')
        except Exception as e:
            logger.log(repr(e))
        finally:
            self._context.post(self, msg.DEPLOYMENT_DONE)

    async def _ensure_map(self):
        if not await io.file_exists(self._map_file):
            await jobh.JobProcess.run_job(self._context, self, (
                self._executable,
                '--create', self._map_file,
                '--map-gen-settings', self._map_gen_settings,
                '--map-settings', self._map_settings))
        autosave_dir = self._runtime_dir + '/saves'
        if not await io.symlink_exists(autosave_dir):
            await io.create_symlink(autosave_dir, self._save_dir)

    # pylint: disable=too-many-locals
    async def _sync_mods(self):
        logger = msglog.LogPublisher(self._context, self)
        mods = util.get('mods', objconv.json_to_dict(await io.read_file(self._mods_list)))
        if not mods:
            logger.log('Mod sync disabled')
            return
        live_mod_list, mod_list = self._mods_dir + '/mod-list.json', []
        for mod in [m for m in mods if m['name'] in _BASE_MOD_NAMES]:
            mod_list.append(util.filter_dict(mod, ('name', 'enabled')))
        settings = objconv.json_to_dict(await io.read_file(self._server_settings))
        if not util.get('username', settings) or not util.get('token', settings):
            logger.log('Unable to sync mods, credentials unavailable')
            if len(mods) == len(mod_list):
                logger.log('Writing live mod config, base game only')
                await io.write_file(live_mod_list, objconv.obj_to_json(dict(mods=mod_list)))
            return
        logger.log('SYNCING mods...')
        baseurl, mod_files = 'https://mods.factorio.com', []
        connector, timeout = aiohttp.TCPConnector(family=socket.AF_INET), aiohttp.ClientTimeout(total=8.0)
        credentials = '?username=' + util.get('username', settings) + '&token=' + util.get('token', settings)
        async with aiohttp.ClientSession(connector=connector) as session:
            for mod in [m for m in mods if m['name'] not in _BASE_MOD_NAMES]:
                mod_list.append(util.filter_dict(mod, ('name', 'enabled')))
                mod_meta_url = baseurl + '/api/mods/' + mod['name']
                async with session.get(mod_meta_url, timeout=timeout) as meta_resp:
                    assert meta_resp.status == 200
                    meta = await meta_resp.json()
                if not util.get('version', mod):
                    mod['version'] = meta['releases'][-1]['version']
                release = util.single([r for r in meta['releases'] if r['version'] == mod['version']])
                if release:
                    mod_files.append(release['file_name'])
                    filename = self._mods_dir + '/' + release['file_name']
                    if not await io.file_exists(filename):
                        logger.log('DOWNLOADING ' + release['file_name'])
                        download_url = baseurl + release['download_url'] + credentials
                        async with session.get(download_url, read_bufsize=io.DEFAULT_CHUNK_SIZE) as modfile_resp:
                            assert modfile_resp.status == 200
                            tracker, content_length = None, modfile_resp.headers.get('Content-Length')
                            if content_length:
                                tracker = msglog.PercentTracker(
                                    self._context, int(content_length), notifications=5, prefix='downloaded')
                            await io.stream_write_file(
                                filename, io.WrapReader(modfile_resp.content),
                                io.DEFAULT_CHUNK_SIZE, self._tempdir, tracker)
                else:
                    logger.log(
                        'ERROR Mod ' + mod['name'] + ' version ' + mod['version'] + ' not found, see ' + mod_meta_url)
        for file in await io.directory_list(self._mods_dir):
            if file['type'] == 'file' and file['name'].endswith(_ZIP) and file['name'] not in mod_files:
                logger.log('Deleting unused mod file ' + file['name'])
                await io.delete_file(self._mods_dir + '/' + file['name'])
        logger.log('Writing live mod config, base game and mods')
        await io.write_file(live_mod_list, objconv.obj_to_json(dict(mods=mod_list)))

    async def restore_autosave(self, filename: str):
        logger = msglog.LogPublisher(self._context, self)
        map_backup = self._save_dir + '/' + _AUTOSAVE_PREFIX + '_' + _MAP + '_backup' + _ZIP
        try:
            self._context.post(self, msg.DEPLOYMENT_START)
            filename = filename[1:] if filename[0] == '/' else filename
            logger.log('RESTORING ' + filename)
            autosave_file = self._save_dir + '/' + filename
            if not await io.file_exists(autosave_file):
                raise FileNotFoundError(autosave_file)
            autosave_size = await io.file_size(autosave_file)
            tracker = msglog.PercentTracker(self._context, autosave_size, notifications=4)
            if await io.file_exists(self._map_file):
                if map_backup == autosave_file:
                    await io.delete_file(self._map_file)
                else:
                    await io.delete_file(map_backup)
                    await io.rename_path(self._map_file, map_backup)
            await io.stream_copy_file(autosave_file, self._map_file, io.DEFAULT_CHUNK_SIZE * 2, self._tempdir, tracker)
            logger.log('Autosave ' + filename + ' restored')
            await funcutil.silently_call(io.delete_file(map_backup))
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
        version = util.get('beta', data, 'stable')
        tasks.task_fork(self._deployment.install_runtime(version), 'factorio.install_runtime()')
        url = util.get('baseurl', data, '') + subscription_path
        return dict(url=url)


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
