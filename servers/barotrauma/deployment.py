# ALLOW core.*
from core.util import io
from core.context import contextsvc
from core.proc import proch, prcenc, wrapper

# BAROTRAUMA https://barotraumagame.com/wiki/Hosting_a_Dedicated_Server
# TODO Try using gnome-terminal.wrapper or whatever is on ubuntu server

# REQUIRED /home/bsalis/.local/share/Daedalic Entertainment GmbH/Barotrauma
# export LD_LIBRARY_PATH=./linux64:$LD_LIBRARY_PATH
# export SteamAppID=1026340
# https://unix.stackexchange.com/questions/43945/whats-the-difference-between-various-term-variables
# Command and "L�*" not found


class Deployment:
    _APP_ID = 1026340

    def __init__(self, context: contextsvc.Context):
        self._mailer = context
        self._python, self._wrapper = context.config('python'), None
        self._home_dir = context.config('home')
        self._runtime_dir = self._home_dir + '/runtime'
        self._executable = self._runtime_dir + '/DedicatedServer'
        self._world_dir = self._home_dir + '/world'
        self._logs_dir = self._world_dir + '/ServerLogs'
        self._env = context.config('env').copy()
        self._env['TERM'] = 'screen'
        self._env['SteamAppID'] = str(Deployment._APP_ID)
        self._env['LD_LIBRARY_PATH'] = self._runtime_dir + '/linux64'

    async def initialise(self):
        await io.create_directories(self._env['HOME'] + '/.local/share/Daedalic Entertainment GmbH/Barotrauma')
        self._wrapper = await wrapper.write_wrapper(self._home_dir)
        await self.build_world()

    def new_server_process(self) -> proch.ServerProcess:
        return proch.ServerProcess(self._mailer, '/usr/bin/python3.10') \
            .use_env(self._env) \
            .use_out_decoder(prcenc.PtyLineDecoder()) \
            .append_arg(self._wrapper) \
            .append_arg(self._executable)

    async def build_world(self):
        await io.create_directory(self._world_dir)
        await io.create_directory(self._logs_dir)
