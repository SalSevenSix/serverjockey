# ALLOW core.* palworld.messaging
from core.util import io, steamutil
from core.msg import msgext, msgftr, msglog
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch, jobh
from core.common import steam, interceptors, portmapper, rconsvc
# from servers.palworld import messaging as msg


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._user_home_dir = context.env('HOME')
        self._home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'

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
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 730, anon=False), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('world-meta', httpext.FileMtimeHandler(self._runtime_dir + '/Pal/Saved/SaveGames'))
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
        # r.pop()
        # r.psh('config')
        # r.put('cmdargs', httpext.FileSystemHandler(self._cmdargs_file), 'm')

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
        await io.create_directory(self._backups_dir, self._world_dir)
        # if not await io.directory_exists(self._runtime_dir):
        #     return
        # if not await io.file_exists(self._cmdargs_file):
        #     await io.write_file(self._cmdargs_file, objconv.obj_to_json(_default_cmdargs(), pretty=True))
