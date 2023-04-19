from core.util import util, io
from core.context import contextsvc
from core.msg import msgftr, msgext
from core.http import httpabc, httprsc, httpstm, httpext
from core.proc import procabc, proch, jobh

# https://github.com/SmartlyDressedGames/U3-Docs/blob/master/ServerHosting.md#How-to-Launch-Server-on-Linux
# https://unturned.info/Server-Hosting/ServerHosting/


class Deployment:

    @staticmethod
    def _default_cmdargs():
        return {
            '_comment_scope': 'Server scope. Options are InternetServer or LanServer',
            'scope': 'InternetServer'
        }

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._python, self._wrapper = context.config('python'), None
        self._home_dir = context.config('home')
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
        self._env = context.config('env').copy()
        self._env['TERM'] = 'xterm'
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir + '/linux64'

    async def initialise(self):
        self._wrapper = await procabc.unpack_wrapper(self._home_dir)
        await self.build_world()
        self._mailer.register(msgext.CallableSubscriber(
            msgftr.Or(httpext.WipeHandler.FILTER_DONE, msgext.Unpacker.FILTER_DONE, jobh.JobProcess.FILTER_DONE),
            self.build_world))
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer), msgext.SyncReply.AT_START))

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('logs', httpext.FileSystemHandler(self._logs_dir)) \
            .append('*{path}', httpext.FileSystemHandler(self._logs_dir, 'path')) \
            .pop() \
            .push('config') \
            .append('cmdargs', httpext.FileSystemHandler(self._cmdargs_file)) \
            .append('commands', httpext.FileSystemHandler(self._commands_file)) \
            .append('settings', httpext.FileSystemHandler(self._settings_file)) \
            .append('workshop', httpext.FileSystemHandler(self._workshop_file)) \
            .pop() \
            .push('deployment') \
            .append('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile)) \
            .append('install-runtime', httpstm.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 1110390)) \
            .append('wipe-runtime', httpext.WipeHandler(self._mailer, self._runtime_dir)) \
            .append('wipe-world-all', httpext.WipeHandler(self._mailer, self._world_dir)) \
            .append('wipe-world-save', httpext.WipeHandler(self._mailer, self._map_dir)) \
            .append('backup-runtime', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._runtime_dir)) \
            .append('backup-world', httpext.ArchiveHandler(self._mailer, self._backups_dir, self._world_dir)) \
            .append('restore-backup', httpext.UnpackerHandler(self._mailer, self._backups_dir, self._home_dir)) \
            .pop() \
            .push('backups', httpext.FileSystemHandler(self._backups_dir)) \
            .append('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'))

    async def new_server_process(self) -> proch.ServerProcess:
        cmdargs = util.json_to_dict(await io.read_file(self._cmdargs_file))
        return proch.ServerProcess(self._mailer, self._python) \
            .use_env(self._env) \
            .use_out_decoder(procabc.PtyLineDecoder()) \
            .append_arg(self._wrapper) \
            .append_arg(self._executable) \
            .append_arg('-batchmode') \
            .append_arg('-nographics') \
            .append_arg('+' + cmdargs['scope'] + '/Save')

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._logs_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._savesvr_dir)
        if not await io.directory_exists(self._runtime_dir):
            return
        if not await io.file_exists(self._cmdargs_file):
            await io.write_file(self._cmdargs_file, util.obj_to_json(Deployment._default_cmdargs(), pretty=True))
        logs_dir = self._runtime_dir + '/Logs'
        if not await io.symlink_exists(logs_dir):
            await io.create_symlink(logs_dir, self._logs_dir)
        servers_dir = self._runtime_dir + '/Servers'
        await io.create_directory(servers_dir)
        save_dir = servers_dir + '/Save'
        if not await io.symlink_exists(save_dir):
            await io.create_symlink(save_dir, self._save_dir)
