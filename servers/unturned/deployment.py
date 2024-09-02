# ALLOW core.* unturned.messaging
from core.util import gc, util, io, objconv
from core.msg import msgftr, msgext, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch, jobh, prcenc, wrapper
from core.common import steam, interceptors, portmapper
from servers.unturned import messaging as msg


def _default_cmdargs():
    return {
        '_comment_scope': 'Server scope. Options are InternetServer or LanServer',
        'scope': 'InternetServer',
        '_comment_upnp': 'Try to automatically redirect ports on home network using UPnP',
        'upnp': True
    }


# https://github.com/SmartlyDressedGames/U3-Docs/blob/master/ServerHosting.md#How-to-Launch-Server-on-Linux
# https://unturned.info/Server-Hosting/ServerHosting/
class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._python, self._wrapper = context.config('python'), None
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._runtime_metafile = self._runtime_dir + '/steamapps/appmanifest_1110390.acf'
        self._executable = self._runtime_dir + '/Unturned_Headless.x86_64'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/logs'
        self._save_dir = self._world_dir + '/save'
        self._savesvr_dir = self._save_dir + '/Server'
        self._map_dir = self._save_dir + '/Level'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._settings_file = self._save_dir + '/Config.json'
        self._workshop_file = self._save_dir + '/WorkshopDownloadConfig.json'
        self._commands_file = self._savesvr_dir + '/Commands.dat'
        self._env = context.env()
        self._env['TERM'] = 'xterm'
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir + '/linux64'

    async def initialise(self):
        self._wrapper = await wrapper.write_wrapper(self._home_dir)
        await self.build_world()
        self._mailer.register(portmapper.PortMapperService(self._mailer))
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer, self._tempdir), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer, self._tempdir), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('logs', httpext.FileSystemHandler(self._logs_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'), 'r')
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_file), 'm')
        r.put('commands', httpext.FileSystemHandler(self._commands_file), 'm')
        r.put('settings', httpext.FileSystemHandler(self._settings_file), 'm')
        r.put('workshop', httpext.FileSystemHandler(self._workshop_file), 'm')
        r.pop()
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 1110390), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('world-meta', httpext.MtimeHandler().check(self._map_dir).dir(self._logs_dir))
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._map_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tempdir=self._tempdir,
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')

    async def new_server_process(self) -> proch.ServerProcess:
        if not await io.file_exists(self._executable):
            raise FileNotFoundError('Unturned game server not installed. Please Install Runtime first.')
        cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        if util.get('upnp', cmdargs, True):
            await self._map_ports()
        return proch.ServerProcess(self._mailer, self._python) \
            .use_env(self._env) \
            .use_out_decoder(prcenc.PtyLineDecoder()) \
            .append_arg(self._wrapper).append_arg(self._executable) \
            .append_arg('-batchmode').append_arg('-nographics') \
            .append_arg('+' + util.get('scope', cmdargs, 'InternetServer') + '/Save')

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._logs_dir, self._save_dir, self._savesvr_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        logs_dir = self._runtime_dir + '/Logs'
        if not await io.symlink_exists(logs_dir):
            await io.create_symlink(logs_dir, self._logs_dir)
        servers_dir = self._runtime_dir + '/Servers'
        await io.create_directory(servers_dir)
        save_dir = servers_dir + '/Save'
        if not await io.symlink_exists(save_dir):
            await io.create_symlink(save_dir, self._save_dir)

    async def _map_ports(self):
        port_key, port = 'port', msg.DEFAULT_PORT
        if await io.file_exists(self._commands_file):
            commands = await io.read_file(self._commands_file)
            for line in commands.split('\n'):
                if line and line.lower().startswith(port_key):
                    port = int(util.lchop(line.lower(), port_key))
        portmapper.map_port(self._mailer, self, port, gc.UDP, 'Unturned query')
        portmapper.map_port(self._mailer, self, port + 1, gc.UDP, 'Unturned server')
