from core.util import io
from core.context import contextsvc
from core.proc import proch


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._runtime_dir = self._home_dir + '/runtime'
        self._executable = self._runtime_dir + '/Unturned_Headless.x86_64'
        self._world_dir = self._home_dir + '/world'
        self._env = context.config('env').copy()
        self._env['TERM'] = 'xterm'
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir + '/linux64'

    async def initialise(self):
        await self.build_world()

    def new_server_process(self) -> proch.ServerProcess:
        return proch.ServerProcess(self._mailer, self._executable) \
            .use_env(self._env) \
            .append_arg('+LanServer/MyServer')
            # .append_arg('-batchmode') \
            # .append_arg('-nographics') \

    async def build_world(self):
        await io.create_directory(self._world_dir)
