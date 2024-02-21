# ALLOW core.* palworld.messaging
from core.util import io, steamutil, objconv
from core.msg import msgext, msgftr, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch, jobh
from core.common import steam, interceptors, portmapper, rconsvc
# from servers.palworld import messaging as msg


def _default_cmdargs():
    return {
        '_comment_port': 'Port number used to listen to the server. Default is 8211',
        'port': None,
        '_comment_publicip': 'Manually specify the global IP address of the network on which the server running.',
        'publicip': None,
        '_comment_publicport': 'Manually specify the port number of the network on which the server running.',
        'publicport': None,
        '_comment_players': 'Maximum number of participants on the server. Default is 32',
        'players': None,
        '_comment_useperfthreads': 'Improves performance in multi-threaded CPU environments.',
        'useperfthreads': False,
        '_comment_NoAsyncLoadingThread': 'Improves performance in multi-threaded CPU environments.',
        'NoAsyncLoadingThread': False,
        '_comment_UseMultithreadForDS': 'Improves performance in multi-threaded CPU environments.',
        'UseMultithreadForDS': False,
        '_comment_EpicAppPalServer': 'Setup server as a community server.',
        'EpicAppPalServer': False
    }


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._user_home_dir = context.env('HOME')
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'
        self._config_dir = self._world_dir + '/Config'
        self._cmdargs_file = self._world_dir + '/cmdargs.json'
        self._settings_file = self._config_dir + '/PalWorldSettings.ini'

    async def initialise(self):
        await steamutil.link_steamclient_to_sdk(self._user_home_dir)
        await self.build_world()
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(portmapper.PortMapperService(self._mailer))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer, self._tempdir), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer, self._tempdir), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_2394010.acf'))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 2394010), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('world-meta', httpext.FileMtimeHandler(self._world_dir + '/SaveGames'))
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._world_dir + '/SaveGames'), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        # r.pop()
        # r.psh('logs', httpext.FileSystemHandler(self._logs_dir))
        # r.put('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path'), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(
            self._backups_dir, 'path', tempdir=self._tempdir,
            read_tracker=msglog.IntervalTracker(self._mailer, initial_message='SENDING data...', prefix='sent'),
            write_tracker=msglog.IntervalTracker(self._mailer)), 'm')
        r.pop()
        r.psh('config')
        r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_file), 'm')
        r.put('settings', httpext.FileSystemHandler(self._settings_file), 'm')

    async def new_server_process(self):
        executable = self._runtime_dir + '/PalServer.sh'
        if not await io.file_exists(executable):
            raise FileNotFoundError('PalWorld game server not installed. Please Install Runtime first.')
        # cmdargs = objconv.json_to_dict(await io.read_file(self._cmdargs_file))
        # server_port = util.get('-port', cmdargs, 27015)
        # if util.get('upnp', cmdargs, True):
        #     portmapper.map_port(self._mailer, self, server_port, portmapper.TCP, 'CS2 TCP server')
        rconsvc.RconService.set_config(self._mailer, self, 25575, 'europa')
        return proch.ServerProcess(self._mailer, executable).use_cwd(self._runtime_dir)

    async def build_world(self):
        await io.create_directory(self._backups_dir, self._world_dir, self._config_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
        saved_dir = self._runtime_dir + '/Pal/Saved'
        if not await io.symlink_exists(saved_dir):
            await io.create_symlink(saved_dir, self._world_dir)
        if not await io.file_exists(self._settings_file):  # TODO also check exists but empty
            data = await io.read_file(self._runtime_dir + '/DefaultPalWorldSettings.ini')
            data = [o for o in data.split('\n') if o and o[0] != ';']
            await io.write_file(self._settings_file, '\n'.join(data))


class PalWorldSettingsIni:
    pass
