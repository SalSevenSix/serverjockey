import logging
# ALLOW core.* hytale.messaging
from core.util import gc, util, tasks, io, aggtrf, objconv, linenc
from core.msg import msgabc, msglog
from core.msgc import sc
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext, httpsubs
from core.system import svrsvc
from core.proc import proch
from core.common import svrhelpers, portmapper
from servers.hytale import messaging as msg, updatecheck as uck, installer as ins

_EXT_MOD_ARCHIVE = 'jar', 'zip'
_EXT_MOD_CONFIG = 'json', 'toml', 'yaml', 'yml'


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
        'server_upnp': True,
        '_comment_check_update_minutes': 'Check for server updates frequency, use zero to disable',
        'check_update_minutes': 360,
        '_comment_event_expressions': 'Regular expressions to extract events from console log',
        'event_expressions': msg.default_event_expressions()
    }


def _default_mods() -> dict:
    services = [dict(type='modtale-v1', endpoint='https://api.modtale.net', mods=['', '', ''])]
    return {'enabled': True, 'ignoreServerVersion': True, 'services': services}


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._runtime_meta = self._runtime_dir + '/versions.json'
        self._java_dir = self._runtime_dir + '/java'
        self._java_exe = self._java_dir + '/bin/java'
        self._server_dir = self._runtime_dir + '/server'
        self._server_jar = self._server_dir + '/Server/HytaleServer.jar'
        self._world_dir = self._home_dir + '/world'
        self._autobackups_dir = self._world_dir + '/backups'
        self._logs_dir = self._world_dir + '/logs'
        self._mods_dir = self._world_dir + '/mods'
        self._save_dir = self._world_dir + '/universe'
        self._worlds_dir = self._save_dir + '/worlds'
        self._map_dir = self._worlds_dir + '/default'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._mods_file = self._world_dir + '/mods.json'
        self._installer = ins.Installer(
            context, self._tempdir, self._runtime_dir, self._runtime_meta, self._server_dir, self._server_jar,
            self._java_dir, self._java_exe, self._mods_dir, self._mods_file)

    async def initialise(self):
        helper = await svrhelpers.DeploymentInitHelper(self._context, self.build_world).init()
        helper.init_ports().init_archiving(self._tempdir).done()
        tasks.task_fork(self._load_user_uuids(), 'hytale.load_user_uuids()')

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta_runtime(self._runtime_meta)
        builder.put_meta_world(httpext.MtimeHandler().check(self._map_dir + '/resources').dir(self._logs_dir))
        builder.put_installer(_InstallRuntimeHandler(self, self._context))
        builder.put_wipes(self._runtime_dir, dict(
            all=self._world_dir, logs=self._logs_dir, autobackups=self._autobackups_dir,
            save=dict(path=self._map_dir, ls_filter=_ls_onlydir)))
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
            cmdargs=self._cmdargs_file, mods=self._mods_file, settings=self._world_dir + '/config.json',
            permissions=self._world_dir + '/permissions.json', bans=self._world_dir + '/bans.json',
            whitelist=self._world_dir + '/whitelist.json', memories=self._save_dir + '/memories.json',
            warps=self._save_dir + '/warps.json'))
        builder.psh('universe', httpext.FileSystemHandler(self._worlds_dir, ls_filter=_ls_onlydir))
        builder.put('*{path}', httpext.FileSystemHandler(self._worlds_dir, 'path', ls_filter=_ls_wconfig), 'm')
        builder.pop()
        builder.psh('mod')
        builder.psh('files', httpext.FileSystemHandler(self._mods_dir, ls_filter=_ls_mfile))
        builder.put('*{path}', httpext.FileSystemHandler(
            self._mods_dir, 'path', ls_filter=_ls_mfile, tempdir=self._tempdir), 'm')
        builder.pop()
        builder.psh('configs', httpext.FileSystemHandler(self._mods_dir, ls_filter=_ls_onlydir))
        builder.put('*{path}', httpext.FileSystemHandler(
            self._mods_dir, 'path', ls_filter=_ls_mconfig, tempdir=self._tempdir), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._server_jar):
            raise FileNotFoundError('Hytale game server not installed. Please Install Runtime first.')
        svrsvc.ServerStatus.notify_state(self._context, self, sc.START)  # pushing early because slow pre-start tasks
        cmdargs, jreargs, svrargs = await self._load_args()
        await self._installer.install_mods()
        self._map_ports(cmdargs)
        self._set_event_expressions(cmdargs)
        uck.set_check_update_minutes(self._context, self, util.get('check_update_minutes', cmdargs))
        server = proch.ServerProcess(self._context, self._java_exe)
        server.use_cwd(self._world_dir).use_out_decoder(linenc.PtyLineDecoder())
        server.append_arg('-XX:AOTCache=' + self._server_dir + '/Server/HytaleServer.aot')
        server.append_struct(jreargs)
        server.append_arg('-jar').append_arg(self._server_jar)
        server.append_arg('--assets').append_arg(self._server_dir + '/Assets.zip')
        server.append_arg('--universe').append_arg(self._save_dir)
        server.append_arg('--backup-dir').append_arg(self._autobackups_dir)
        server.append_struct(svrargs)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir, self._mods_dir,
                                  self._autobackups_dir, self._save_dir, self._worlds_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        await io.keyfill_json_file(self._cmdargs_file, _default_cmdargs())
        if not await io.file_exists(self._mods_file):
            await io.write_file(self._mods_file, objconv.obj_to_json(_default_mods(), pretty=True))

    async def _load_args(self) -> tuple:
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        jreargs, svrargs, cmdargs = {}, {}, util.delete_dict(cmdargs, (
            '-b', '-t', '-jar', '--version', '--help', '--assets', '--universe', '--backup-dir'))
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

    def _set_event_expressions(self, cmdargs: dict):
        event_expressions = util.get('event_expressions', cmdargs)
        if event_expressions and isinstance(event_expressions, dict):
            self._context.post(self, msg.EVENT_EXPRESSIONS, event_expressions)

    async def _load_user_uuids(self):
        players_dir = self._save_dir + '/players'
        try:
            if not await io.directory_exists(players_dir):
                return
            players = await io.directory_list(players_dir)
            players = [e['name'] for e in players if util.fext(e['name']) == 'json']
            for player in players:
                name = objconv.json_to_dict(await io.read_file(players_dir + '/' + player))
                name = util.get('Text', util.get('Nameplate', util.get('Components', name)))
                if name:
                    self._context.post(self, msg.USER_UUID, (player[0:-5], name))
                else:
                    logging.warning('hytale.load_user_uuids(%s) failed processing file %s', players_dir, player)
        except Exception as e:
            logging.error('hytale.load_user_uuids(%s) failed %s', players_dir, repr(e))

    async def install_runtime(self, version: str):
        try:
            self._context.post(self, msg.DEPLOYMENT_START)
            self._installer.log('START Install')
            await self._installer.install_runtime(version)
            await self.build_world()
            self._installer.log('END Install')
        except Exception as e:
            self._installer.log(repr(e))
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
        tasks.task_fork(self._deployment.install_runtime(util.get('beta', data)), 'hytale.install_runtime()')
        url = util.get('baseurl', data, '') + subscription_path
        return dict(url=url)


def _ls_onlydir(entry) -> bool:
    return entry['type'] == 'directory'


def _ls_wconfig(entry) -> bool:
    return entry['name'] == 'config.json'


def _ls_mfile(entry) -> bool:
    ftype, fname, fext = entry['type'], entry['name'], util.fext(entry['name'])
    return fname and ftype == 'file' and fext in _EXT_MOD_ARCHIVE


def _ls_mconfig(entry) -> bool:
    if _ls_onlydir(entry):
        return True
    ftype, fname, fext = entry['type'], entry['name'], util.fext(entry['name'])
    return fname and ftype == 'file' and (fext in _EXT_MOD_CONFIG or fext.startswith(_EXT_MOD_CONFIG[0]))


def _ls_autobackups(entry) -> bool:
    return entry['type'] == 'file' and util.fext(entry['name']) == 'zip'
