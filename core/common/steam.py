import logging
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.util import aggtrf, util
from core.msg import msgabc
from core.http import httpabc, httpext, httpsubs
from core.proc import jobh


class SteamCmdInstallHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, path: str, app_id: int):
        self._mailer = mailer
        self._path = path
        self._app_id = app_id
        self._handler = httpext.MessengerHandler(self._mailer, jobh.JobProcess.REQUEST, selector=httpsubs.Selector(
            msg_filter=jobh.JobProcess.FILTER_ALL_LINES,
            completed_filter=jobh.JobProcess.FILTER_DONE,
            aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        script = _script_head()
        if util.get('wipe', data):
            script += 'rm -rf ' + self._path + '\n'
        script += '$(find_steamcmd) +force_install_dir ' + self._path
        script += ' +login anonymous +app_update ' + str(self._app_id)
        beta = util.get('beta', data)
        if beta:
            script += ' -beta ' + util.script_escape(beta)
        if util.get('validate', data):
            script += ' validate'
        script += ' +quit'
        logging.debug('SCRIPT\n' + script)
        data['script'] = script
        return await self._handler.handle_post(resource, data)


def _script_head() -> str:
    return '''find_steamcmd() {
  /usr/games/steamcmd +quit >/dev/null 2>&1 && echo /usr/games/steamcmd && return 0
  ~/Steam/steamcmd.sh +quit >/dev/null 2>&1 && echo ~/Steam/steamcmd.sh && return 0
  echo steamcmd && return 1
}
echo "Installing or updating runtime with SteamCMD"
echo "Log updates are usually delayed"
'''
