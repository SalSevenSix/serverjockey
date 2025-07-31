# ALLOW core.* valheim.messaging
from core.util import gc, util, io, objconv, idutil
from core.context import contextsvc
from core.http import httprsc, httpext
from core.proc import proch
from core.common import portmapper, svrhelpers
from servers.valheim import messaging as msg

APPID = '896660'


def _default_cmdargs():
    return {
        '_comment_port': 'Specify server port, note port+1 also used',
        '-port': msg.DEFAULT_PORT,
        '_comment_upnp': 'Try to automatically redirect ports on home network using UPnP',
        'upnp': True,
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
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._save_dir = self._world_dir + '/worlds_local'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._adminlist_file = self._world_dir + '/adminlist.txt'
        self._bannedlist_file = self._world_dir + '/bannedlist.txt'
        self._permittedlist_file = self._world_dir + '/permittedlist.txt'
        self._env = context.env()
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir + '/linux64'
        self._env['SteamAppId'] = '892970'

    async def initialise(self):
        await self.build_world()
        helper = svrhelpers.DeploymentInitHelper(self._context, self.build_world)
        helper.init_ports().init_jobs().init_archiving(self._tempdir)
        helper.init_logging(self._logs_dir, msg.CONSOLE_LOG_FILTER).done()

    def resources(self, resource: httprsc.WebResource):
        builder = svrhelpers.DeploymentResourceBuilder(self._context, resource).psh_deployment()
        builder.put_meta(self._runtime_dir + '/steamapps/appmanifest_' + APPID + '.acf',
                         httpext.MtimeHandler().check(self._save_dir).dir(self._logs_dir))
        builder.put_installer_steam(self._runtime_dir, APPID)
        builder.put_wipes(self._runtime_dir, dict(save=self._save_dir, logs=self._logs_dir, all=self._world_dir))
        builder.put_archiving(self._home_dir, self._backups_dir, self._runtime_dir, self._world_dir)
        builder.pop()
        builder.put_logs(self._logs_dir)
        builder.put_backups(self._tempdir, self._backups_dir)
        builder.put_config(dict(
            cmdargs=self._cmdargs_file, adminlist=self._adminlist_file,
            permittedlist=self._permittedlist_file, bannedlist=self._bannedlist_file))

    async def new_server_process(self) -> proch.ServerProcess:
        executable = self._runtime_dir + '/valheim_server.x86_64'
        if not await io.file_exists(executable):
            raise FileNotFoundError('Valheim game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        await self._map_ports(cmdargs)
        server = proch.ServerProcess(self._context, executable)
        server.use_cwd(self._runtime_dir).use_env(self._env)
        server.append_arg('-nographics').append_arg('-batchmode')
        server.append_arg('-savedir').append_arg(self._world_dir)
        server.append_struct(util.delete_dict(cmdargs, (
            'upnp', '-nographics', '-batchmode', '-savedir', '-world', '-logFile', '-instanceid')))
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))

    async def _map_ports(self, cmdargs: dict):
        port = util.get('port', cmdargs)
        port = port if port else msg.DEFAULT_PORT
        self._context.post(self, msg.NAME_PORT, port)
        if util.get('upnp', cmdargs, True):
            portmapper.map_port(self._context, self, port, gc.UDP, 'Valheim server')
            portmapper.map_port(self._context, self, port + 1, gc.UDP, 'Valheim query')
