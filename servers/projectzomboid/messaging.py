# ALLOW core.*
from core.util import util, dtutil
from core.msg import msgabc, msglog, msgftr, msgext
from core.context import contextsvc
from core.system import svrsvc, svrext
from core.proc import proch, jobh, prcext
from core.common import cachelock, playerstore

_CHAT_KEY_STRING = 'New message \'ChatMessage{chat=General'
_MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
_READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('*** SERVER STARTED ***'))
CONSOLE_LOG_FILTER = msgftr.Or(
    msgftr.And(
        proch.ServerProcess.FILTER_ALL_LINES,
        msgftr.Not(msgftr.Or(
            msgftr.DataStrContains('password', True),
            msgftr.DataStrContains('token', True),
            msgftr.DataStrContains('command entered via server console', True)))),
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS,
    cachelock.FILTER_NOTIFICATIONS)
CONSOLE_OUTPUT_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.Not(msgftr.DataStrContains(_CHAT_KEY_STRING)))
SERVER_RESTART_REQUIRED = 'messaging.RESTART_REQUIRED'
SERVER_RESTART_REQUIRED_FILTER = msgftr.NameIs(SERVER_RESTART_REQUIRED)


def initialise(context: contextsvc.Context):
    context.register(prcext.ServerStateSubscriber(context))
    context.register(svrext.MaintenanceStateSubscriber(context, _MAINTENANCE_STATE_FILTER, _READY_STATE_FILTER))
    context.register(playerstore.PlayersSubscriber(context))
    context.register(_ServerDetailsSubscriber(context))
    context.register(_PlayerEventSubscriber(context))
    context.register(_PlayerChatSubscriber(context))
    context.register(_ProvideAdminPasswordSubscriber(context, context.config('secret')))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION = '> version='
    VERSION_FILTER = msgftr.DataStrContains(VERSION)
    IP = 'Public IP:'
    IP_FILTER = msgftr.DataStrContains(IP)
    PORT = '> Clients should use'
    PORT_FILTER = msgftr.DataStrContains(PORT)
    INGAMETIME = '> IngameTime'
    INGAMETIME_FILTER = msgftr.DataStrContains(INGAMETIME)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            SERVER_RESTART_REQUIRED_FILTER,
            msgftr.And(
                CONSOLE_OUTPUT_FILTER,
                msgftr.Or(_ServerDetailsSubscriber.INGAMETIME_FILTER,
                          _ServerDetailsSubscriber.VERSION_FILTER,
                          _ServerDetailsSubscriber.IP_FILTER,
                          _ServerDetailsSubscriber.PORT_FILTER))))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.INGAMETIME)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ingametime': value})
            return None
        if SERVER_RESTART_REQUIRED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'restart': dtutil.to_millis(message.created())})
            return None
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.VERSION)
            value = util.right_chop_and_strip(value, 'demo=')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.IP)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': value})
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.PORT)
            value = util.right_chop_and_strip(value, 'port for connections')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'port': int(value)})
            return None
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    LOGIN, LOGOUT = '> ConnectionManager: [fully-connected]', '> Disconnected player'
    LOGIN_FILTER, LOGOUT_FILTER = msgftr.DataStrContains(LOGIN), msgftr.DataStrContains(LOGOUT)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            CONSOLE_OUTPUT_FILTER,
            msgftr.Or(_PlayerEventSubscriber.LOGIN_FILTER,
                      _PlayerEventSubscriber.LOGOUT_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            steamid = util.left_chop_and_strip(message.data(), 'steam-id=')
            steamid = util.right_chop_and_strip(steamid, 'access=')
            steamid = util.right_chop_and_strip(steamid, '(owner=')
            name = util.left_chop_and_strip(message.data(), 'username="')
            name = util.right_chop_and_strip(name, '" connection-type=')
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name, steamid)
            return None
        if _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            parts = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.LOGOUT).split(' ')
            steamid, name = parts[-1], ' '.join(parts[:-1])
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name[1:-1], steamid)
            return None
        return None


# New message 'ChatMessage{chat=General, author='Sal', text='Helo Everyone'}' was sent members of chat '0'

class _PlayerChatSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.DataStrContains(_CHAT_KEY_STRING)))
        self._mailer = mailer

    def handle(self, message):
        name = util.left_chop_and_strip(message.data(), 'author=')
        name = util.right_chop_and_strip(name, ', text=')
        text = util.left_chop_and_strip(message.data(), ', text=')
        text = util.right_chop_and_strip(text, '}\' was sent members of chat')
        playerstore.PlayersSubscriber.event_chat(self._mailer, self, name[1:-1], text[1:-1])
        return None


class _ProvideAdminPasswordSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer, pwd: str):
        super().__init__(msgftr.And(
            CONSOLE_OUTPUT_FILTER,
            msgftr.Or(msgftr.DataStrContains('Enter new administrator password'),
                      msgftr.DataStrContains('Confirm the password'))))
        self._mailer = mailer
        self._pwd = pwd

    async def handle(self, message):
        await proch.PipeInLineService.request(self._mailer, self, self._pwd, force=True)
        return None
