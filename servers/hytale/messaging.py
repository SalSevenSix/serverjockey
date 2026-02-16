# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.common import svrhelpers, playerstore

SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('Hytale Server Booted!'))
DEPLOYMENT_START, DEPLOYMENT_DONE = 'Deployment.Start', 'Deployment.Done'
FILTER_DEPLOYMENT_START, FILTER_DEPLOYMENT_DONE = msgftr.NameIs(DEPLOYMENT_START), msgftr.NameIs(DEPLOYMENT_DONE)
CONSOLE_LOG_FILTER = msgftr.Or(mc.ServerProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, msgftr.DataMatches(r'^\[.*(ERROR|SEVERE)\].*'))
UPDATE_REQUIRED = 'messaging.UPDATE_REQUIRED'
UPDATE_REQUIRED_FILTER = msgftr.NameIs(UPDATE_REQUIRED)


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state(FILTER_DEPLOYMENT_START, FILTER_DEPLOYMENT_DONE).init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))
    context.register(_ServerAuthSubscriber(context))
    context.register(_InstallAuthSubscriber(context))


# [2026/01/24 12:51:45   INFO]   [HytaleServer] Booting up HytaleServer - Version: 2026.01.17-4b0f30090, Revision: 4b0f3
# [2026/01/24 12:52:15   INFO]   [ServerManager|P] Listening on /[0:0:0:0:0:0:0:0]:5520 and took 31ms 322us 14ns
# [2026/01/24 12:52:15   INFO]   [ServerManager|P] Listening on /0.0.0.0:5520 and took 9ms 693us 147ns
# [2026/01/24 12:52:15   INFO]   [ServerManager|P] Listening on /[0:0:0:0:0:0:0:1]:5520 and took 6ms 331us 742ns
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*\[HytaleServer\] Booting up HytaleServer - Version: (.*?), Revision.*')
    PORT_FILTER = msgftr.DataMatches(r'.*\[ServerManager.*Listening on \/\d+\.\d+\.\d+\.\d+:(.*?) and took.*')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.Or(UPDATE_REQUIRED_FILTER, msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerDetailsSubscriber.VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER))))
        self._mailer, self.public_ip = mailer, public_ip

    def handle(self, message):
        if UPDATE_REQUIRED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(notice='Server Update Required'))
        elif _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            port = _ServerDetailsSubscriber.PORT_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self.public_ip, port=port))
        return None


# [2026/01/24 08:54:05   INFO]   [World|default] Player 'SalSevenSix' joined world 'default' at location Vector3d{x=143.
# [2026/01/24 08:55:01   INFO]   [Hytale] SalSevenSix: Hello everyone
# [2026/02/06 15:22:45   INFO]   [Universe|P] Removing player 'SalSevenSix' (dd8d4c6b-64e9-4f49-aa45-387f7450f5e2)
# [2026/01/24 08:55:07   INFO]   [PlayerSystems] Removing player 'SalSevenSix (SalSevenSix)' from world 'default' (dd8d4
# [2026/02/07 07:21:09   INFO]   [Gravestones|P] [Gravestones] Created for SalSevenSix at (1322, 119, -83)
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    LOGIN_FILTER = msgftr.DataMatches(r".*INFO\]\s*\[World\|default\] Player '(.*?)' joined world 'default'.*")
    CHAT_FILTER = msgftr.DataMatches(r'.*INFO\]\s*\[Hytale\] (.*?): (.*?)$')
    LOGOUT_FILTER = msgftr.DataMatches(r".*INFO\]\s*\[Universe.*\] Removing player '(.*?)' \(.*\)$")
    DEATH_FILTER = msgftr.DataMatches(r'.*INFO\]\s*\[Gravestones.*\].* Created for (.*?) at \((.*?)\)$')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            msgftr.And(
                mc.ServerProcess.FILTER_STDOUT_LINE,
                msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER, _PlayerEventSubscriber.LOGIN_FILTER,
                          _PlayerEventSubscriber.LOGOUT_FILTER, _PlayerEventSubscriber.DEATH_FILTER)),
            playerstore.EVENT_CLEAR_FILTER))
        self._mailer, self._player_names = mailer, []

    def handle(self, message):
        if playerstore.EVENT_CLEAR_FILTER.accepts(message):
            self._player_names = []
        elif _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.CHAT_FILTER.find_all(message.data()), 2)
            if name and name in self._player_names:
                playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        elif _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LOGIN_FILTER.find_one(message.data())
            if name and name not in self._player_names:
                self._player_names.append(name)
                playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
        elif _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LOGOUT_FILTER.find_one(message.data())
            if name and name in self._player_names:
                self._player_names.remove(name)
                playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        elif _PlayerEventSubscriber.DEATH_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.DEATH_FILTER.find_all(message.data()), 2)
            if name and name in self._player_names:
                text = 'location ' + text.replace(' ', '') if text else None
                playerstore.PlayersSubscriber.event_death(self._mailer, self, name, text)
        return None


# [2026/01/25 08:48:59   WARN]   [HytaleServer] No server tokens configured. Use /auth login to authenticate.
# [2026/01/25 08:56:59   INFO]   [AbstractCommand] Or visit: https://oauth.accounts.hytale.com/oauth2/device/verify?user
#   _code=...
# [2026/01/25 09:51:11   INFO]   [ServerAuthManager] Authentication successful! Mode: OAUTH_DEVICE
# Authentication successful! Use '/auth status' to view details.
# WARNING: Credentials stored in memory only - they will be lost on restart!
# To persist credentials, run: /auth persistence <type>
# Available types: Memory, Encrypted
# Credential storage changed to: Encrypted
# Server logged out. Previous mode: OAUTH_STORE
class _ServerAuthSubscriber(msgabc.AbcSubscriber):
    NOAUTH_FILTER = msgftr.DataMatches(r'.*WARN\]\s*\[HytaleServer\].*Use \/auth login to authenticate.$')
    VERIFY_FILTER = msgftr.DataMatches(r'.*INFO\]\s*\[AbstractCommand\] Or visit: (.*?)$')
    AUTHED_FILTER = msgftr.DataMatches(r'.*INFO\]\s*\[ServerAuthManager\] Authentication successful! Mode: (.*?)$')
    MODE_FILTER = msgftr.DataMatches(r'^Credential storage changed to: (.*?)$')
    UNSAVED_FILTER = msgftr.DataEquals('WARNING: Credentials stored in memory only - they will be lost on restart!')
    LOGOUT_FILTER = msgftr.DataStrStartsWith('Server logged out.')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerAuthSubscriber.NOAUTH_FILTER, _ServerAuthSubscriber.VERIFY_FILTER,
                      _ServerAuthSubscriber.AUTHED_FILTER, _ServerAuthSubscriber.MODE_FILTER,
                      _ServerAuthSubscriber.UNSAVED_FILTER, _ServerAuthSubscriber.LOGOUT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _ServerAuthSubscriber.NOAUTH_FILTER.accepts(message) or _ServerAuthSubscriber.LOGOUT_FILTER.accepts(message):
            self._notify_auth(dict(type='cmd', value='Login Device', data='auth login device'))
        elif _ServerAuthSubscriber.VERIFY_FILTER.accepts(message):
            url = _ServerAuthSubscriber.VERIFY_FILTER.find_one(message.data())
            if url.startswith('https://oauth.accounts.hytale.com/oauth2/device/verify?user_code='):
                self._notify_auth(dict(type='url', value='Authorise Device', data=url))
        elif _ServerAuthSubscriber.AUTHED_FILTER.accepts(message):
            mode = _ServerAuthSubscriber.AUTHED_FILTER.find_one(message.data())
            self._notify_auth(f'Authenticated ({mode})')
        elif _ServerAuthSubscriber.MODE_FILTER.accepts(message):
            mode = _ServerAuthSubscriber.MODE_FILTER.find_one(message.data())
            self._notify_auth(f'Authenticated ({mode})')
        elif _ServerAuthSubscriber.UNSAVED_FILTER.accepts(message):
            self._notify_auth(dict(type='cmd', value='Persist Authentication', data='auth persistence Encrypted'))
        return None

    def _notify_auth(self, value: str | dict):
        svrsvc.ServerStatus.notify_details(self._mailer, self, dict(auth=value))


# https://oauth.accounts.hytale.com/oauth2/device/verify?user_code=...
# downloading latest ("release" patchline) to "/home/bsalis/serverjockey/ht/runtime/server.zip"
class _InstallAuthSubscriber(msgabc.AbcSubscriber):
    VERIFY_FILTER = msgftr.DataStrStartsWith('https://oauth.accounts.hytale.com/oauth2/device/verify?user_code=')
    AUTHED_FILTER = msgftr.DataStrStartsWith('downloading')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            msglog.LogPublisher.LOG_FILTER,
            msgftr.Or(_InstallAuthSubscriber.VERIFY_FILTER, _InstallAuthSubscriber.AUTHED_FILTER)))
        self._mailer, self._verifying = mailer, False

    def handle(self, message):
        if _InstallAuthSubscriber.VERIFY_FILTER.accepts(message):
            self._verifying, auth = True, dict(type='url', value='Authorise Device', data=message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(auth=auth))
        elif self._verifying and _InstallAuthSubscriber.AUTHED_FILTER.accepts(message):
            self._verifying, auth = False, 'Authorised Device'
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(auth=auth))
