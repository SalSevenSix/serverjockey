import logging
from core.util import aggtrf, util
from core.msg import msgabc
from core.http import httpabc, httpext, httpsubs
from core.proc import jobh, shell   # TODO Should not import proc package in http package


class SteamCmdInstallHandler(httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, path: str, app_id: int):
        self._mailer = mailer
        self._path = path
        self._app_id = app_id
        self._handler = httpext.MessengerHandler(self._mailer, jobh.JobProcess.START, selector=httpsubs.Selector(
            msg_filter=jobh.JobProcess.FILTER_ALL_LINES,
            completed_filter=jobh.JobProcess.FILTER_JOB_DONE,
            aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        script = shell.Script()
        if util.get('wipe', data):
            script.include_delete_path(self._path)
        script.include_steamcmd_app_update(
            app_id=self._app_id,
            install_dir=self._path,
            beta=util.script_escape(util.get('beta', data)),
            validate=util.get('validate', data))
        script.include_softlink_steamclient_lib(self._path)
        script = script.build()
        logging.debug('SCRIPT\n' + script)
        data['script'] = script
        return await self._handler.handle_post(resource, data)
