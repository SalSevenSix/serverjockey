# ALLOW core.* starbound.messaging
from core.util import io
from core.msg import msgext, msgftr
from core.context import contextsvc
from core.http import httpabc, httprsc, httpext
from core.proc import proch, jobh
from core.common import steam, interceptors

# STARBOUND https://starbounder.org/Guide:LinuxServerSetup


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._world_dir = self._home_dir + '/world'

    async def initialise(self):
        await self.build_world()
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        r = httprsc.ResourceBuilder(resource)
        r.reg('r', interceptors.block_running_or_maintenance(self._mailer))
        r.reg('m', interceptors.block_maintenance_only(self._mailer))
        r.put('log', httpext.FileSystemHandler(self._world_dir + '/starbound_server.log'))
        r.psh('logs', httpext.FileSystemHandler(self._world_dir, ls_filter=_logfiles))
        r.put('*{path}', httpext.FileSystemHandler(self._world_dir, 'path'))
        r.pop()
        r.psh('config')
        r.put('settings', httpext.FileSystemHandler(self._world_dir + '/starbound_server.config'))
        r.pop()
        r.psh('deployment')
        r.put('runtime-meta', httpext.FileSystemHandler(self._runtime_dir + '/steamapps/appmanifest_211820.acf'))
        r.put('install-runtime', steam.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 211820, anon=False), 'r')
        r.put('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir), 'r')
        r.put('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir), 'r')
        r.put('wipe-world-save', httpext.WipeHandler(self._mailer, self._world_dir + '/universe'), 'r')
        r.put('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir), 'r')
        r.put('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir), 'r')
        r.put('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir), 'r')
        r.pop()
        r.psh('backups', httpext.FileSystemHandler(self._backups_dir))
        r.put('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'), 'm')

    def new_server_process(self):
        bin_dir = self._runtime_dir + '/linux'
        return proch.ServerProcess(self._mailer, bin_dir + '/starbound_server').use_cwd(bin_dir)

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        storage_dir = self._runtime_dir + '/storage'
        if not await io.symlink_exists(storage_dir):
            await io.create_symlink(storage_dir, self._world_dir)


def _logfiles(entry) -> bool:
    return entry['type'] == 'file' and entry['name'].startswith('starbound_server.log')
