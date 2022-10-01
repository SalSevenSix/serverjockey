from core.util import io
from core.msg import msgftr, msgtrf, msglog, msgext
from core.context import contextsvc
from core.http import httpabc, httprsc, httpstm, httpext, httpsel
from core.proc import proch, jobh
from core.system import svrsvc
from servers.sevendaystodie import messaging as msg


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._backups_dir = self._home_dir + '/backups'
        self._runtime_dir = self._home_dir + '/runtime'
        self._runtime_metafile = self._runtime_dir + '/steamapps/appmanifest_294420.acf'
        self._executable = self._runtime_dir + '/7DaysToDieServer.x86_64'
        self._world_dir = self._home_dir + '/world'
        self._config_dir = self._world_dir + '/config'
        self._save_dir = self._world_dir + '/save'
        self._log_dir = self._save_dir + '/logs'
        self._log_file = self._log_dir + '/server-%Y%m%d%H%M%S.log'
        self._config_file = self._config_dir + '/serverconfig.xml'
        self._env = context.config('env').copy()
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir

    async def initialise(self):
        await self.build_world()
        self._mailer.register(jobh.JobProcess(self._mailer))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Archiver(self._mailer), msgext.SyncReply.AT_START))
        self._mailer.register(
            msgext.SyncWrapper(self._mailer, msgext.Unpacker(self._mailer), msgext.SyncReply.AT_START))
        self._mailer.register(msglog.LogfileSubscriber(
            self._log_file,
            msg.CONSOLE_LOG_FILTER,
            msgftr.And(msgftr.NameIs(svrsvc.ServerStatus.NOTIFY_RUNNING), msgftr.DataEquals(False)),
            msgtrf.GetData()))

    def resources(self, resource: httpabc.Resource):
        httprsc.ResourceBuilder(resource) \
            .push('logs', httpext.FileSystemHandler(self._log_dir)) \
            .append('*{path}', httpext.FileSystemHandler(self._log_dir, 'path')) \
            .pop() \
            .push('config') \
            .append('settings', httpext.FileSystemHandler(self._config_file)) \
            .pop() \
            .push('deployment') \
            .append('runtime-meta', httpext.FileSystemHandler(self._runtime_metafile)) \
            .append('install-runtime', httpstm.SteamCmdInstallHandler(self._mailer, self._runtime_dir, 294420)) \
            .append('wipe-runtime', httpext.WipeHandler(self._runtime_dir)) \
            .append('wipe-world-all', httpext.WipeHandler(self._world_dir, self.build_world)) \
            .append('wipe-world-config', httpext.WipeHandler(self._config_dir, self.build_world)) \
            .append('wipe-world-save', httpext.WipeHandler(self._save_dir, self.build_world)) \
            .append('backup-runtime', httpext.MessengerHandler(
                self._mailer, msgext.Archiver.REQUEST,
                {'backups_dir': self._backups_dir, 'source_dir': self._runtime_dir}, httpsel.archive_selector())) \
            .append('backup-world', httpext.MessengerHandler(
                self._mailer, msgext.Archiver.REQUEST,
                {'backups_dir': self._backups_dir, 'source_dir': self._world_dir}, httpsel.archive_selector())) \
            .append('restore-backup', httpext.MessengerHandler(
                self._mailer, msgext.Unpacker.REQUEST,
                {'backups_dir': self._backups_dir, 'root_dir': self._home_dir}, httpsel.unpacker_selector())) \
            .pop() \
            .push('backups', httpext.FileSystemHandler(self._backups_dir)) \
            .append('*{path}', httpext.FileSystemHandler(self._backups_dir, 'path'))

    def new_server_process(self) -> proch.ServerProcess:
        return proch.ServerProcess(self._mailer, self._executable) \
            .use_env(self._env) \
            .append_arg('-quit') \
            .append_arg('-batchmode') \
            .append_arg('-nographics') \
            .append_arg('-dedicated') \
            .append_arg('-configfile=' + self._config_file)

    async def build_world(self):
        await io.create_directory(self._backups_dir)
        await io.create_directory(self._world_dir)
        await io.create_directory(self._config_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._log_dir)
