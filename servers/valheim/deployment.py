import socket
import aiohttp
# ALLOW core.* valheim.messaging
from core.util import gc, util, io, objconv, idutil, funcutil, pack
from core.context import contextsvc
from core.msg import msglog
from core.msgc import sc
from core.http import httpabc, httprsc, httpext, httpsec
from core.system import svrsvc
from core.proc import proch
from core.common import portmapper, svrhelpers
from servers.valheim import messaging as msg

APPID = '896660'
_EXTS = 'db', 'fwl'


def _default_cmdargs() -> dict:
    return {
        '_comment_port': 'Specify server port, note port+1 also used',
        '-port': msg.DEFAULT_PORT,
        '_comment_upnp': 'Try to automatically redirect ports on home network using UPnP',
        'upnp': True,
        '_comment_bepinex_url': 'Thunderstore URL to download BepInEx mod framework to install if needed',
        'bepinex_url': 'https://thunderstore.io/package/download/denikson/BepInExPack_Valheim/5.4.2350/',
        '_comment_name': 'Name of your server that will be visible in the server listing',
        '-name': 'My Server',
        '_comment_password': 'Password needed by players to join server (required)',
        '-password': idutil.generate_token(10),
        '_comment_public': 'Server visibility: 1 to show in public list, 0 for join by IP only',
        '-public': 1,
        '_comment_crossplay': 'Allow non-Steam users to join server',
        '-crossplay': False,
        '_comment_preset': 'Use world preset: normal, casual, easy, hard, hardcore, immersive, hammer',
        '-preset': None,
        '_comment_modifier': 'Set individual world modifiers, overrides preset',
        '-modifier': {
            '_comment_combat': 'Options: veryeasy, easy, hard, veryhard',
            'combat': None,
            '_comment_deathpenalty': 'Options: casual, veryeasy, easy, hard, hardcore',
            'deathpenalty': None,
            '_comment_resources': 'Options: muchless, less, more, muchmore, most',
            'resources': None,
            '_comment_raids': 'Options: none, muchless, less, more, muchmore',
            'raids': None,
            '_comment_portals': 'Options: casual, hard, veryhard',
            'portals': None
        },
        '_comment_setkey': 'Set world modifier checkbox key: nobuildcost, playerevents, passivemobs, nomap',
        '-setkey': None,
        '_comment_saveinterval': 'World save interval in seconds, default 1800',
        '-saveinterval': None,
        '_comment_backups': 'Number of automatic backups kept, default 4',
        '-backups': None,
        '_comment_backupshort': 'Interval between first automatic backup, default 7200',
        '-backupshort': None,
        '_comment_backuplong': 'Interval between subsequent automatic backups, default 43200',
        '-backuplong': None
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._bepinex_dir = self._runtime_dir + '/BepInEx'
        self._bepplug_dir = self._bepinex_dir + '/plugins'
        self._bepconf_dir = self._bepinex_dir + '/config'
        self._bepconf_file = self._bepconf_dir + '/BepInEx.cfg'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._cache_dir = self._world_dir + '/cache'
        self._save_dir = self._world_dir + '/worlds_local'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._adminlist_file = self._world_dir + '/adminlist.txt'
        self._bannedlist_file = self._world_dir + '/bannedlist.txt'
        self._permittedlist_file = self._world_dir + '/permittedlist.txt'
        self._env = context.env()
        self._env['DOORSTOP_ENABLED'] = '1'
        self._env['DOORSTOP_TARGET_ASSEMBLY'] = './BepInEx/core/BepInEx.Preloader.dll'
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir + './linux64:./doorstop_libs'
        self._env['LD_PRELOAD'] = 'libdoorstop_x64.so'
        self._env['SteamAppId'] = '892970'

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_ports().init_jobs().init_archiving(self._tempdir)
        helper.init_logging(self._logs_dir, msg.CONSOLE_LOG_FILTER).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf',
                         httpext.MtimeHandler().check(self._save_dir).dir(self._logs_dir))
        builder.put_installer_steam(self._runtime_dir, APPID)
        builder.put_wipes(self._runtime_dir, dict(
            save=self._save_dir, autobackups=dict(path=self._save_dir, ls_filter=_ls_autobackups_all),
            cache=self._cache_dir, logs=self._logs_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.put_restore_autobackup(_RestoreAutobackupHandler(self))
        builder.pop()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_autobackups_handler(_AutobackupsHandler(self))
        builder.put_config(dict(
            cmdargs=self._cmdargs_file, adminlist=self._adminlist_file,
            permittedlist=self._permittedlist_file, bannedlist=self._bannedlist_file))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/valheim_server.x86_64'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Valheim game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        await self._install_bepinex(cmdargs)
        self._map_ports(cmdargs)
        server = proch.ServerProcess(self._context, executable)
        server.use_cwd(self._runtime_dir).use_env(self._env)
        server.append_arg('-nographics').append_arg('-batchmode')
        server.append_arg('-savedir').append_arg(self._world_dir)
        server.append_struct(util.delete_dict(cmdargs, (
            'upnp', 'bepinex_url', '-nographics', '-batchmode', '-savedir', '-world', '-logFile', '-instanceid')))
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        await io.create_directory(self._bepinex_dir, self._bepconf_dir, self._bepplug_dir)
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))

    def _map_ports(self, cmdargs: dict):
        port = util.get('port', cmdargs)
        port = port if port else msg.DEFAULT_PORT
        self._context.post(self, msg.NAME_PORT, port)
        if util.get('upnp', cmdargs, True):
            portmapper.map_port(self._context, self, port, gc.UDP, 'Valheim server')
            portmapper.map_port(self._context, self, port + 1, gc.UDP, 'Valheim query')

    async def _install_bepinex(self, cmdargs: dict):
        logger = msglog.LogPublisher(self._context, self)
        if await io.file_exists(self._bepconf_file):
            logger.log('INFO BepInEx already installed')
            return
        if len(await io.directory_list(self._bepplug_dir)) == 0:
            logger.log('INFO No plugins found, BepInEx will not be installed')
            return
        url = util.get('bepinex_url', cmdargs)
        if not url:
            logger.log('WARNING bepinex_url not found in Launch Options, plugins will not work')
            return
        workdir = self._tempdir + '/' + idutil.generate_id()
        zipfile, unpacked = workdir + '/bepinex.zip', workdir + '/bepinex'
        source = unpacked + '/BepInExPack_Valheim'
        try:
            svrsvc.ServerStatus.notify_state(self._context, self, sc.START)
            logger.log('INSTALL START BepInEx plugin framework')
            await io.create_directory(workdir)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                              ' AppleWebKit/537.36 (KHTML, like Gecko)'
                              ' Chrome/120.0.0.0 Safari/537.36'}
            connector = aiohttp.TCPConnector(family=socket.AF_INET)  # force IPv4
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers, read_bufsize=io.DEFAULT_CHUNK_SIZE) as response:
                    assert response.status == 200
                    await io.stream_write_file(zipfile, io.WrapReader(response.content),
                                               io.DEFAULT_CHUNK_SIZE, self._tempdir)
            await io.create_directory(unpacked)
            await pack.unpack_archive(zipfile, unpacked)
            files = [str(e['name']) for e in await io.directory_list(source)]
            files = [n for n in files if util.fext(n) != 'sh']
            for name in files:
                await io.delete_any(self._runtime_dir + '/' + name)
                await io.move_path(source + '/' + name, self._runtime_dir + '/' + name)
        finally:
            await funcutil.silently_call(io.delete_directory(workdir))
            logger.log('INSTALL END BepInEx plugin framework')

    async def autobackups(self, baseurl: str) -> tuple:
        if await io.directory_exists(self._save_dir + '/Dedicated'):  # v1 save format
            result = [e for e in await io.directory_list(self._save_dir, baseurl) if _ls_autobackups_new(e)]
            for entry in result:
                entry['type'] = 'file'
            return tuple(result)
        if await io.file_exists(self._save_dir + '/Dedicated.' + _EXTS[0]):  # old save format
            files = [e for e in await io.directory_list(self._save_dir, baseurl) if _ls_autobackups_old(e)]
            alts = [util.fname_only(e['name']) for e in files if util.fext(e['name']) == _EXTS[1]]
            result = [e for e in files if util.fext(e['name']) == _EXTS[0] and util.fname_only(e['name']) in alts]
            for entry in result:
                entry['name'] = util.fname_only(entry['name'])
            return tuple(result)
        return ()

    async def restore_autobackup(self, filename: str) -> bool:
        path = self._save_dir + '/' + util.fname_only(filename)
        if await io.directory_exists(path):  # v1 save format
            await io.copy_directory(path, self._save_dir + '/Dedicated')
        elif await io.file_exists(path + '.' + _EXTS[0]):  # old save format
            backups, targets = [], []
            for ext in _EXTS:
                backups.append(path + '.' + ext)
                targets.append(self._save_dir + '/Dedicated.' + ext)
            for path in backups:
                if not await io.file_exists(path):
                    return False
            for index in (0, 1):
                await io.stream_copy_file(backups[index], targets[index], tempdir=self._tempdir)
        return True


class _AutobackupsHandler(httpabc.GetHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        return await self._deployment.autobackups(data['baseurl'] + resource.path(data))


class _RestoreAutobackupHandler(httpabc.PostHandler):

    def __init__(self, deployment: Deployment):
        self._deployment = deployment

    async def handle_post(self, resource, data):
        filename = util.get('filename', data)
        if not filename:
            return httpabc.ResponseBody.BAD_REQUEST
        result = await self._deployment.restore_autobackup(filename)
        return httpabc.ResponseBody.NO_CONTENT if result else httpabc.ResponseBody.NOT_FOUND


def _ls_autobackups_new(entry) -> bool:
    ftype, fname = entry['type'], entry['name']
    return fname and fname.startswith('Dedicated_backup') and ftype == 'directory'


def _ls_autobackups_old(entry) -> bool:
    ftype, fname, fext = entry['type'], entry['name'], util.fext(entry['name'])
    return fname and fname.startswith('Dedicated_backup') and ftype == 'file' and fext in _EXTS


def _ls_autobackups_all(entry) -> bool:
    return _ls_autobackups_new(entry) or _ls_autobackups_old(entry)
