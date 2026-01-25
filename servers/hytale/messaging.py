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


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state(FILTER_DEPLOYMENT_START, FILTER_DEPLOYMENT_DONE).init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))
    context.register(_AuthStatusSubscriber(context))


# [2026/01/24 12:51:45   INFO]   [HytaleServer] Booting up HytaleServer - Version: 2026.01.17-4b0f30090, Revision: 4b0f3
# [2026/01/24 12:52:15   INFO]   [ServerManager|P] Listening on /[0:0:0:0:0:0:0:0]:5520 and took 31ms 322us 14ns
# [2026/01/24 12:52:15   INFO]   [ServerManager|P] Listening on /0.0.0.0:5520 and took 9ms 693us 147ns
# [2026/01/24 12:52:15   INFO]   [ServerManager|P] Listening on /[0:0:0:0:0:0:0:1]:5520 and took 6ms 331us 742ns
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*\[HytaleServer\] Booting up HytaleServer - Version: (.*?), Revision.*')
    PORT_FILTER = msgftr.DataMatches(r'.*\[ServerManager.*Listening on \/\d+\.\d+\.\d+\.\d+:(.*?) and took.*')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerDetailsSubscriber.VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer, self.public_ip = mailer, public_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            port = _ServerDetailsSubscriber.PORT_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self.public_ip, port=port))
        return None


# [2026/01/24 08:54:05   INFO]   [World|default] Player 'SalSevenSix' joined world 'default' at location Vector3d{x=143.
# [2026/01/24 08:55:01   INFO]   [Hytale] SalSevenSix: Hello everyone
# [2026/01/24 08:55:07   INFO]   [PlayerSystems] Removing player 'SalSevenSix (SalSevenSix)' from world 'default' (dd8d4
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    LOGIN_FILTER = msgftr.DataMatches(r".*INFO\]\s*\[World\|default\] Player '(.*?)' joined world 'default'.*")
    CHAT_FILTER = msgftr.DataMatches(r'.*INFO\]\s*\[Hytale\] (.*?): (.*?)$')
    LOGOUT_FILTER = msgftr.DataMatches(
        r".*INFO\]\s*\[PlayerSystems\] Removing player '(.*?) \(.*\)' from world 'default'.*")

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.LOGIN_FILTER,
                      _PlayerEventSubscriber.LOGOUT_FILTER)))
        self._mailer, self._player_names = mailer, set()

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.CHAT_FILTER.find_all(message.data()), 2)
            if name in self._player_names:
                playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        elif _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LOGIN_FILTER.find_one(message.data())
            self._player_names.add(name)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
        elif _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LOGOUT_FILTER.find_one(message.data())
            if name in self._player_names:
                self._player_names.remove(name)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        return None


# [2026/01/25 08:48:59   WARN]   [HytaleServer] No server tokens configured. Use /auth login to authenticate.
# [2026/01/25 08:56:59   INFO]   [AbstractCommand] Or visit: https://oauth.accounts.hytale.com/oauth2/device/verify?user
#   _code=...
# [2026/01/25 09:51:11   INFO]   [ServerAuthManager] Authentication successful! Mode: OAUTH_DEVICE
# Authentication successful! Use '/auth status' to view details.
# WARNING: Credentials stored in memory only - they will be lost on restart!
# To persist credentials, run: /auth persistence <type>
# Available types: Memory, Encrypted
class _AuthStatusSubscriber(msgabc.AbcSubscriber):
    NOAUTH_FILTER = msgftr.DataMatches(r'.*WARN\]\s*\[HytaleServer\].*Use \/auth login to authenticate.$')
    VERIFY_FILTER = msgftr.DataMatches(r'.*INFO\]\s*\[AbstractCommand\] Or visit: (.*?)$')
    AUTHED_FILTER = msgftr.DataMatches(r'.*INFO\]\s*\[ServerAuthManager\] Authentication successful!.*')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_AuthStatusSubscriber.NOAUTH_FILTER, _AuthStatusSubscriber.VERIFY_FILTER,
                      _AuthStatusSubscriber.AUTHED_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _AuthStatusSubscriber.NOAUTH_FILTER.accepts(message):
            # auth login device
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(auth='Not Authorised'))
        elif _AuthStatusSubscriber.VERIFY_FILTER.accepts(message):
            url = _AuthStatusSubscriber.VERIFY_FILTER.find_one(message.data())
            if url.startswith('https://oauth.accounts.hytale.com/oauth2/device/verify?user_code='):
                svrsvc.ServerStatus.notify_details(self._mailer, self, dict(auth='Verify ' + url))
        elif _AuthStatusSubscriber.AUTHED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(auth='Authorised'))
        return None
