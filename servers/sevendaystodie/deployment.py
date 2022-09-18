from core.util import io
from core.msg import msgftr, msgtrf, msglog
from core.context import contextsvc
from core.proc import proch
from core.system import svrsvc


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._runtime_dir = self._home_dir + '/runtime'
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
        self._mailer.register(msglog.LogfileSubscriber(
            self._log_file,
            msgftr.Or(proch.ServerProcess.FILTER_STDOUT_LINE, proch.ServerProcess.FILTER_STDERR_LINE),
            msgftr.And(msgftr.NameIs(svrsvc.ServerStatus.NOTIFY_RUNNING), msgftr.DataEquals(False)),
            msgtrf.GetData()))

    def new_server_process(self) -> proch.ServerProcess:
        return proch.ServerProcess(self._mailer, self._executable) \
            .use_env(self._env) \
            .append_arg('-quit') \
            .append_arg('-batchmode') \
            .append_arg('-nographics') \
            .append_arg('-dedicated') \
            .append_arg('-configfile=' + self._config_file)

    async def build_world(self):
        await io.create_directory(self._world_dir)
        await io.create_directory(self._config_dir)
        await io.create_directory(self._save_dir)
        await io.create_directory(self._log_dir)
