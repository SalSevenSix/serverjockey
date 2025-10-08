# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import jobh
from core.common import rconsvc, playerstore, svrhelpers

SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('[Info] Root: Writing runtime configuration to'))
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES, rconsvc.RconService.FILTER_OUTPUT,
    jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(mc.ServerProcess.FILTER_ALL_LINES, msgftr.DataStrStartsWith('[Error]'))


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))


# [Info] Server Version 1.4.4 (linux x86_64) Source ID: 8cbe6faf22282659828a194e06a08999f213769e Protocol: 747
# [Info] UniverseServer: listening for incoming TCP connections on 0000:0000:0000:0000:0000:0000:0000:0000:21025
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'^\[Info\] Server Version (.*?) \(.*')
    PORT_FILTER = msgftr.DataMatches(r'^\[Info\] UniverseServer: listening for incoming TCP connections on.*:(\d+)$')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerDetailsSubscriber.VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=version))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            port = _ServerDetailsSubscriber.PORT_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=port))
        return None


# [Info] UniverseServer: Logged in account '<anonymous>' as player 'Jazmin' from address 00:0000:ffff:c0a8:0065
# [Info] UniverseServer: Client 'Jazmin' <1> (0000:0000:0000:0000:0000:ffff:c0a8:0065) connected
# [Info] UniverseServer: Client 'Jazmin' <1> (0000:0000:0000:0000:0000:ffff:c0a8:0065) disconnected for reason:
# [Info] Chat: <Wingshield> Hello Everyone
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT_FILTER = msgftr.DataMatches(r'^\[Info\] Chat: <(.*?)> (.*?)$')
    CONNECT_FILTER = msgftr.DataMatches(r"^\[Info\] UniverseServer: Client '(.*?)' .*connected$")
    DISCONNECT_FILTER = msgftr.DataMatches(r"^\[Info\] UniverseServer: Client '(.*?)' .*disconnected.*")

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.CONNECT_FILTER,
                      _PlayerEventSubscriber.DISCONNECT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            name, text = util.fill(_PlayerEventSubscriber.CHAT_FILTER.find_all(message.data()), 2)
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        elif _PlayerEventSubscriber.CONNECT_FILTER.accepts(message):
            name = _PlayerEventSubscriber.CONNECT_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
        elif _PlayerEventSubscriber.DISCONNECT_FILTER.accepts(message):
            name = _PlayerEventSubscriber.DISCONNECT_FILTER.find_one(message.data())
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
        return None
