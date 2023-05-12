import logging
import vdf
import re
from asyncio import subprocess   # TODO Probably should not import this
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.util import aggtrf, util, io
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


class SteamCmdInstallHandler(httpabc.PostHandler):

    def __init__(self, context: contextsvc.Context, path: str, app_id: int, anon: bool = True):
        self._mailer, self._steam_config = context, _SteamConfig(context.config('env'))
        self._path, self._app_id, self._anon = path, app_id, anon
        self._handler = httpext.MessengerHandler(self._mailer, jobh.JobProcess.REQUEST, selector=httpsubs.Selector(
            msg_filter=jobh.JobProcess.FILTER_ALL_LINES,
            completed_filter=jobh.JobProcess.FILTER_DONE,
            aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        login = 'anonymous' if self._anon else await self._steam_config.get_login()
        if not login:
            raise httpabc.ResponseBody.CONFLICT
        if not self._anon:
            self._mailer.register(_KillSteam(self._mailer))
        script = _script_head()
        if util.get('wipe', data):
            script += 'rm -rf ' + self._path + '\n'
        script += '$(find_steamcmd)'
        script += ' +force_install_dir ' + self._path
        script += ' +login ' + login
        script += ' +app_update ' + str(self._app_id)
        beta = util.get('beta', data)
        if beta:
            script += ' -beta ' + util.script_escape(beta)
        if util.get('validate', data):
            script += ' validate'
        script += ' +quit'
        logging.debug('SCRIPT\n' + script)
        data['command'], data['pty'] = script, True
        return await self._handler.handle_post(resource, data)


class SteamCmdLoginHandler(httpabc.PostHandler):

    def __init__(self, context: contextsvc.Context):
        self._mailer, self._steam_config = context, _SteamConfig(context.config('env'))
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
        logging.debug('SCRIPT\n' + script)
        data['command'], data['pty'] = script, True
        return await self._handler.handle_post(resource, data)


class SteamCmdInputHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        value = util.get('value', data)
        if value:
            result = await jobh.JobPipeInLineService.request(self._mailer, self, util.script_escape(value))
            if isinstance(result, Exception):
                raise result
        print('DING')
        return httpabc.ResponseBody.NO_CONTENT


# Loading Steam API...OK
# Logging in user 'bsalis' to Steam Public...
# password:
# Enter the current code from your Steam Guard Mobile Authenticator app
# Two-factor code:
# OK
# Waiting for client config...OK
# Waiting for user info...OK


class _KillSteam(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            jobh.JobProcess.FILTER_STDOUT_LINE,
            jobh.JobProcess.FILTER_STARTED,
            jobh.JobProcess.FILTER_DONE))
        self._mailer = mailer
        self._process: subprocess.Process | None = None
        self._solicit_password = re.compile('^Logging in user \'.*\' to Steam Public\.\.\.$')

    async def handle(self, message):
        if jobh.JobProcess.FILTER_DONE.accepts(message):
            return True
        if jobh.JobProcess.FILTER_STARTED.accepts(message):
            self._process = message.data()
            return None
        if jobh.JobProcess.FILTER_STDOUT_LINE.accepts(message):
            if self._solicit_password.match(message.data()) is not None:
                if self._process and self._process.returncode is None:
                    self._process.terminate()
                return True
        return None


class _SteamConfig:

    def __init__(self, env: dict):
        self._path = env['HOME'] + '/Steam/config/config.vdf'  # TODO check manual SteamCMD install location

    async def _load(self) -> tuple:
        try:
            result = await io.read_file(self._path)
            root = vdf.loads(result)
            steamer = root['InstallConfigStore']['Software']['Valve']['steam']
            return root, steamer
        except Exception as e:
            logging.debug('Problem loading or parsing ' + self._path + ' ' + repr(e))
        return None, None

    async def get_login(self) -> str | None:
        root, steamer = await self._load()
        if not steamer:
            return None
        if 'Accounts' in steamer:
            for login in steamer['Accounts'].keys():
                return login
        return None

    async def clear_cache(self):
        root, steamer = await self._load()
        if not steamer:
            return
        if 'Accounts' in steamer:
            del steamer['Accounts']
        if 'ConnectCache' in steamer:
            del steamer['ConnectCache']
        await io.write_file(self._path, vdf.dumps(root))
