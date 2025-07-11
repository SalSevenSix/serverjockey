import logging
import asyncio
from asyncio import subprocess
import vdf
# ALLOW util.* msg*.* context.* http.* system.* proc.*
from core.util import steamutil, aggtrf, util, io, tasks
from core.msg import msgabc, msgftr
from core.context import contextsvc
from core.http import httpabc, httpext, httpsubs
from core.proc import jobh


def _script_head() -> str:
    return '''find_steamcmd() {
  /usr/games/steamcmd +quit >/dev/null 2>&1 && echo /usr/games/steamcmd && return 0
  ~/Steam/steamcmd.sh +quit >/dev/null 2>&1 && echo ~/Steam/steamcmd.sh && return 0
  echo steamcmd && return 1
}
echo "Running SteamCMD, log output may be delayed..."
'''


# pylint: disable=logging-not-lazy
def _dump_script(script: str):
    logging.debug('SCRIPT\n' + script)


class SteamCmdInstallHandler(httpabc.PostHandler):

    def __init__(self, context: contextsvc.Context, path: str, app_id: int | str, anon: bool = True):
        self._mailer, self._steam_config = context, _SteamConfig(context.env('HOME'))
        self._path, self._app_id, self._anon = path, str(app_id), anon
        self._handler = httpext.MessengerHandler(self._mailer, jobh.JobProcess.REQUEST, selector=httpsubs.Selector(
            msg_filter=jobh.JobProcess.FILTER_ALL_LINES,
            completed_filter=jobh.JobProcess.FILTER_DONE,
            aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        login = 'anonymous' if self._anon else await self._steam_config.get_login()
        if not login:
            raise httpabc.ResponseBody.CONFLICT
        script = _script_head()
        if util.get('wipe', data):
            script += 'rm -rf ' + self._path + '\n'
        script += '$(find_steamcmd)'
        script += ' +force_install_dir ' + self._path
        script += ' +login ' + login
        script += ' +app_update ' + self._app_id
        beta = util.get('beta', data)
        if beta:
            script += ' -beta ' + util.script_escape(beta)
        if util.get('validate', data):
            script += ' validate'
        script += ' +quit'
        _dump_script(script)
        data['command'], data['pty'] = script, True
        if not self._anon:
            self._mailer.register(_KillSteamOnSolicitPassword())
        return await self._handler.handle_post(resource, data)


class SteamCmdLoginHandler(httpabc.PostHandler):

    def __init__(self, context: contextsvc.Context):
        self._mailer, self._steam_config = context, _SteamConfig(context.env('HOME'))
        self._handler = httpext.MessengerHandler(self._mailer, jobh.JobProcess.REQUEST, selector=httpsubs.Selector(
            msg_filter=jobh.JobProcess.FILTER_ALL_LINES,
            completed_filter=jobh.JobProcess.FILTER_DONE,
            aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        login = util.get('login', data)
        if not login:
            raise httpabc.ResponseBody.BAD_REQUEST
        await self._steam_config.clear_cache()
        script = _script_head()
        script += '$(find_steamcmd)'
        script += ' +login ' + util.script_escape(login)
        script += ' +quit'
        _dump_script(script)
        data['command'], data['pty'] = script, True
        self._mailer.register(_KillSteamOnNoHeartbeat())
        return await self._handler.handle_post(resource, data)


class SteamCmdInputHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        value = util.get('value', data)
        if not value:
            self._mailer.post(self, _KillSteamOnNoHeartbeat.HEARTBEAT)
            return httpabc.ResponseBody.NO_CONTENT
        result = await jobh.JobPipeInLineService.request(self._mailer, self, value)
        if isinstance(result, Exception):
            raise result
        return httpabc.ResponseBody.NO_CONTENT


class _KillSteamOnSolicitPassword(msgabc.AbcSubscriber):

    def __init__(self):
        super().__init__(msgftr.Or(
            jobh.JobProcess.FILTER_STDOUT_LINE, jobh.JobProcess.FILTER_STARTED, jobh.JobProcess.FILTER_DONE))
        self._process: subprocess.Process | None = None

    def handle(self, message):
        if jobh.JobProcess.FILTER_STDOUT_LINE.accepts(message):
            if message.data().find('Cached credentials not found') > -1:
                _terminate_process(self._process)
                return True
        if jobh.JobProcess.FILTER_STARTED.accepts(message):
            self._process = message.data()
            return None
        if jobh.JobProcess.FILTER_DONE.accepts(message):
            return True
        return None


class _KillSteamOnNoHeartbeat(msgabc.AbcSubscriber):
    HEARTBEAT = '_KillSteamOnNoHeartbeat.Hearbeat'
    FILTER_HEARTBEAT = msgftr.NameIs(HEARTBEAT)

    def __init__(self):
        super().__init__(msgftr.Or(
            _KillSteamOnNoHeartbeat.FILTER_HEARTBEAT, jobh.JobProcess.FILTER_STARTED, jobh.JobProcess.FILTER_DONE))
        self._queue, self._task = asyncio.Queue(), None
        self._process: subprocess.Process | None = None

    def handle(self, message):
        if _KillSteamOnNoHeartbeat.FILTER_HEARTBEAT.accepts(message):
            if self._task:
                self._queue.put_nowait(True)
            return None
        if jobh.JobProcess.FILTER_STARTED.accepts(message):
            self._process = message.data()
            self._task = tasks.task_start(self._monitor(), self)
            return None
        if jobh.JobProcess.FILTER_DONE.accepts(message):
            self._queue.put_nowait(False)
            return True
        return None

    async def _monitor(self):
        try:
            looping = True
            while looping:
                looping = await asyncio.wait_for(self._queue.get(), 3.0)
                self._queue.task_done()
        except asyncio.TimeoutError:
            _terminate_process(self._process)
        finally:
            util.clear_queue(self._queue)
            tasks.task_end(self._task)


class _SteamConfig:

    def __init__(self, home_dir: str):
        self._home_dir = home_dir

    async def _load(self) -> tuple:
        try:
            config_path = await steamutil.get_config_path(self._home_dir)
            root = vdf.loads(await io.read_file(config_path))
            valve = root['InstallConfigStore']['Software']['Valve']
            steamer = util.get('Steam', valve, util.get('steam', valve))
            return config_path, root, steamer
        except Exception as e:
            logging.warning('Problem loading or parsing Steam config: %s', repr(e))
        return None, None, None

    async def get_login(self) -> str | None:
        config_path, root, steamer = await self._load()
        if not steamer:
            return None
        if 'Accounts' in steamer:
            for login in steamer['Accounts'].keys():
                return login
        return None

    async def clear_cache(self):
        config_path, root, steamer = await self._load()
        if not steamer:
            return
        if 'Accounts' in steamer:
            del steamer['Accounts']
        if 'ConnectCache' in steamer:
            del steamer['ConnectCache']
        await io.write_file(config_path, vdf.dumps(root))


def _terminate_process(process: subprocess.Process | None):
    if process and process.returncode is None:
        process.terminate()
