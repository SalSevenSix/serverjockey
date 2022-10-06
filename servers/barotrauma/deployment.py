from core.util import io
from core.context import contextsvc
from core.proc import proch


class Deployment:

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._home_dir = context.config('home')
        self._runtime_dir = self._home_dir + '/runtime'
        self._executable = self._runtime_dir + '/DedicatedServer'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/ServerLogs'

    async def initialise(self):
        await self.build_world()

    def new_server_process(self) -> proch.ServerProcess:
        return proch.ServerProcess(self._mailer, self._executable)

    async def build_world(self):
        await io.create_directory(self._world_dir)
        await io.create_directory(self._logs_dir)
