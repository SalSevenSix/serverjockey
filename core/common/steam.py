import logging
import asyncio
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.util import aggtrf, util
from core.msg import msgabc, msgftr
from core.http import httpabc, httpext, httpsubs
from core.proc import jobh


def _script_head() -> str:
    return '''find_steamcmd() {
  /usr/games/steamcmd +quit >/dev/null 2>&1 && echo /usr/games/steamcmd && return 0
  ~/Steam/steamcmd.sh +quit >/dev/null 2>&1 && echo ~/Steam/steamcmd.sh && return 0
  echo steamcmd && return 1
}
echo "Installing or updating runtime with SteamCMD"
echo "Log updates are usually delayed"
'''


class SteamCmdInstallHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, path: str, app_id: int, anon: bool = True):
        self._mailer = mailer
        self._path, self._app_id, self._anon = path, app_id, anon
        self._handler = httpext.MessengerHandler(self._mailer, jobh.JobProcess.REQUEST, selector=httpsubs.Selector(
            msg_filter=jobh.JobProcess.FILTER_ALL_LINES,
            completed_filter=jobh.JobProcess.FILTER_DONE,
            aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        login = 'anonymous'
        if not self._anon:
            login = 'bsalis'  # TODO Get user from _SteamConfig
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


class _SteamConfig:
    pass


# ~/Steam/config/config.vdf ...
#  "ConnectCache"
#  {
#   "f5e8c7a71" "....."
#  }

# Loading Steam API...OK
# Logging in user 'bsalis' to Steam Public...
# password:
# Enter the current code from your Steam Guard Mobile Authenticator app
# Two-factor code:
# OK
# Waiting for client config...OK
# Waiting for user info...OK


class _KillSteamCmdIfSolicitHanged(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer, password: str):
        super().__init__(msgftr.Or(jobh.JobProcess.FILTER_STDOUT_LINE, jobh.JobProcess.FILTER_DONE))
        self._mailer = mailer
        assert password  # TODO test this is ok
        self._password = password
        print('|' + password + '|')

    async def handle(self, message):
        if jobh.JobProcess.FILTER_DONE.accepts(message):
            return True
        print('|' + message.data() + '|')
        if message.data().find("Logging in user 'bsalis' to Steam Public...") > -1:
            await asyncio.sleep(1)
            await jobh.JobPipeInLineService.request(self._mailer, self, self._password)
        return None
