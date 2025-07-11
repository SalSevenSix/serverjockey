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
    VERSION_PREFIX, VERSION_SUFFIX = '[Info] Server Version', 'Source ID:'
    VERSION_FILTER = msgftr.DataMatches(
        '.*' + VERSION_PREFIX.replace('[', r'\[').replace(']', r'\]') + '.*' + VERSION_SUFFIX + '.*')
    PORT_FILTER = msgftr.DataStrContains('[Info] UniverseServer: listening for incoming TCP connections on')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerDetailsSubscriber.VERSION_FILTER, _ServerDetailsSubscriber.PORT_FILTER)))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.rchop(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            value = util.rchop(value, '(')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=value))
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = message.data()
            value = value[value.rfind(':') + 1:]
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=value))
        return None


# [Info] UniverseServer: Logged in account '<anonymous>' as player 'Jazmin' from address 00:0000:ffff:c0a8:0065
# [Info] UniverseServer: Client 'Jazmin' <1> (0000:0000:0000:0000:0000:ffff:c0a8:0065) connected
# [Info] UniverseServer: Client 'Jazmin' <1> (0000:0000:0000:0000:0000:ffff:c0a8:0065) disconnected for reason:
# [Info] Chat: <Wingshield> Hello Everyone
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CHAT = '[Info] Chat: <'
    CHAT_FILTER = msgftr.DataStrContains(CHAT)
    PREFIX = '[Info] UniverseServer: Client'
    REG_PREFIX = '.*' + PREFIX.replace('[', r'\[').replace(']', r'\]')
    CONNECT_FILTER = msgftr.DataMatches(REG_PREFIX + r'.*\) connected.*')
    DISCONNECT_FILTER = msgftr.DataMatches(REG_PREFIX + r'.*\) disconnected for reason.*')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.CONNECT_FILTER,
                      _PlayerEventSubscriber.DISCONNECT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            value = util.lchop(message.data(), _PlayerEventSubscriber.CHAT)
            name = util.rchop(value, '>')
            text = util.lchop(value, '>')
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
            return None
        value = util.lchop(message.data(), _PlayerEventSubscriber.PREFIX)[1:]
        value = util.rchop(value, "' ")
        if _PlayerEventSubscriber.CONNECT_FILTER.accepts(message):
            playerstore.PlayersSubscriber.event_login(self._mailer, self, value)
        elif _PlayerEventSubscriber.DISCONNECT_FILTER.accepts(message):
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, value)
        return None
