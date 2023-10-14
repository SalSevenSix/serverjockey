# ALLOW core.* csgo.messaging
from core.util import util, io, objconv
from core.msg import msgext, msgftr, msglog, msgtrf
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.system import svrsvc
from core.proc import proch, jobh, wrapper
from core.common import steam, interceptors, portmapper, rconsvc
from servers.csgo import messaging as msg


def _default_cmdargs():
    return {
        '_comment_ip': 'IP binding.',
        '-ip': '0.0.0.0',
        '_comment_rcon_password': 'Password to use for rcon, also enables rcon.',
        '+rcon_password': util.generate_token(8),
        '_comment_map': 'Initial map to use.',
        '+map': 'gm_construct',
        '_comment_upnp': 'Try to automatically redirect server port on home network using UPnP.',
        'upnp': True
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._python, self._wrapper = context.config('python'), None
        self._home_dir, self._tmp_dir = context.config('home'), context.config('tmpdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._config_dir, config_dir = self._world_dir + '/cfg', self._runtime_dir + '/garrysmod/cfg'
        self._config_files = []
        self._config_files.append(_ConfigFile('server', 'server.cfg', config_dir, self._config_dir))

    async def initialise(self):
        self._wrapper = await wrapper.write_wrapper(self._home_dir)
        await self.build_world()
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer, self._tmp_dir), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer, self._tmp_dir), msgext.SyncReply.AT_START))
        self._mailer.register(msglog.LogfileSubscriber(
            self._logs_dir + '/%Y%m%d-%H%M%S.log', msg.CONSOLE_LOG_FILTER,
            svrsvc.ServerStatus.RUNNING_FALSE_FILTER, msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_4020.acf'))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 4020), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('logs', httpext.FileSystemHandler(self._logs_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tmp_dir=self._tmp_dir,
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_file), 'm')
        for config_file in self._config_files:
            r.put(config_file.identity(), httpext.FileSystemHandler(config_file.world_path()), 'm')

    async def new_server_process(self):
        executable = self._runtime_dir + '/srcds_run'
        if not await io.file_exists(executable):
            raise FileNotFoundError('CSGO game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        # TODO need to use whatever port it's set to not assume default
        if util.get('upnp', cmdargs, True):
            portmapper.map_port(self._mailer, self, 27015, portmapper.TCP, 'CSGO server')
        rconsvc.RconService.set_config(self._mailer, self, 27015, util.get('+rcon_password', cmdargs))
        server = proch.ServerProcess(self._mailer, self._python)
        server.add_success_rc(2)  # For some reason clean shutdown is rc=2
        server.append_arg(self._wrapper).append_arg(executable)
        server.append_arg('-game').append_arg('garrysmod')
        for key, value in cmdargs.items():
            if key != 'upnp' and not key.startswith('_'):
                if value and isinstance(value, bool):
                    server.append_arg(key)
                else:
                    server.append_arg(key).append_arg(value)
        return server

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir, self._config_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        logs_dir = self._runtime_dir + '/garrysmod/logs'
        if not await io.symlink_exists(logs_dir):
            await io.create_symlink(logs_dir, self._logs_dir)
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        for config_file in self._config_files:
            if not await io.symlink_exists(config_file.runtime_path()):
                runtime_exists = await io.file_exists(config_file.runtime_path())
                world_exists = await io.file_exists(config_file.world_path())
                if runtime_exists and not world_exists:
                    await io.copy_text_file(config_file.runtime_path(), config_file.world_path())
                else:
                    await io.write_file(config_file.world_path(), '')
                await io.create_symlink(config_file.runtime_path(), config_file.world_path())


class _ConfigFile:

    def __init__(self, identity: str, name: str, runtime_path: str, world_path: str):
        self._identity, self._name = identity, name
        self._runtime_path = runtime_path + '/' + name
        self._world_path = world_path + '/' + name

    def identity(self):
        return self._identity

    def name(self):
        return self._name

    def runtime_path(self):
        return self._runtime_path

    def world_path(self):
        return self._world_path
