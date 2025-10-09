# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import playerstore, svrhelpers

SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('INF StartGame done'))
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES, jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.DataMatches(r'^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d \d*\.\d* ERR .*'))


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))


# 2025-10-09T09:53:19 0.001 INF Version: V 2.4 (b6) Compatibility Version: V 2.4, Build: LinuxServer 64 Bit
# GamePref.ServerPort = 26900
# GamePref.WebDashboardPort = 8080
# 2025-10-09T09:55:58 159.351 INF [Web] Started Webserver on port 8080
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*INF Version: (.*?) Compatibility Version.*')
    PORT_FILTER = msgftr.DataMatches(r'^GamePref.ServerPort = (\d+)$')
    CON_PORT_FILTER = msgftr.DataMatches(r'.*INF \[Web\] Started Webserver on port (\d+)$')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _ServerDetailsSubscriber.CON_PORT_FILTER)))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            port = _ServerDetailsSubscriber.PORT_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=port))
        elif _ServerDetailsSubscriber.CON_PORT_FILTER.accepts(message):
            cport = _ServerDetailsSubscriber.CON_PORT_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(cport=cport))
        return None


# 2024-08-14T19:39:28 236.252 INF GMSG: Player 'Apollo' joined the game
# 2024-12-18T11:50:33 369.738 INF Chat (from 'Steam_76561197968989085', entity id '171', to 'Global'): 'Apollo': hello
# 2024-08-14T19:39:45 253.490 INF GMSG: Player 'Apollo' left the game
# 2024-11-29T23:49:36 252.509 INF GMSG: Player 'Apollo' died
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT_FILTER = msgftr.DataMatches(r".*INF Chat.*to 'Global'\): '(.*?)': (.*?)$")
    JOIN_FILTER = msgftr.DataMatches(r".*INF GMSG: Player '(.*?)' joined the game$")
    LEAVE_FILTER = msgftr.DataMatches(r".*INF GMSG: Player '(.*?)' left the game$")
    DEATH_FILTER = msgftr.DataMatches(r".*INF GMSG: Player '(.*?)' died$")

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.LEAVE_FILTER,
                      _PlayerEventSubscriber.DEATH_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.CHAT_FILTER.find_all(message.data()), 2)
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        elif _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            name = _PlayerEventSubscriber.JOIN_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
        elif _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            name = _PlayerEventSubscriber.LEAVE_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        elif _PlayerEventSubscriber.DEATH_FILTER.accepts(message):
            name = _PlayerEventSubscriber.DEATH_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_death(self._mailer, self, name)
        return None
