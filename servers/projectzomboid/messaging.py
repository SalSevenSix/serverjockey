# ALLOW core.*
from core.util import util, dtutil, objconv
from core.msg import msgabc, msglog, msgftr, msgext
from core.msgc import mc
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
    mc.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('*** SERVER STARTED ***'))
CONSOLE_LOG_FILTER = msgftr.Or(
    msgftr.And(
        mc.ServerProcess.FILTER_ALL_LINES,
        msgftr.Not(msgftr.Or(
            msgftr.DataStrContains('password', True),
            msgftr.DataStrContains('token', True),
            msgftr.DataStrContains('command entered via server console', True)))),
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS,
    cachelock.FILTER_NOTIFICATIONS)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.Or(msgftr.DataStrStartsWith('ERROR:'), msgftr.DataStrStartsWith('SEVERE:')))
CONSOLE_OUTPUT_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE,
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
            value = util.lchop(message.data(), _ServerDetailsSubscriber.INGAMETIME)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ingametime=value))
            return None
        if SERVER_RESTART_REQUIRED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(restart=dtutil.to_millis(message.created())))
            return None
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION)
            value = util.rchop(value, 'demo=')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=value))
            return None
        if _ServerDetailsSubscriber.IP_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.IP)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=value))
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.PORT)
            value = util.rchop(value, 'port for connections')
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(port=objconv.to_int(value)))
            return None
        return None


# LOG  : Network     , 1732903690678> 21,508,632> [30-11-24 01:08:10.678] > ConnectionManager: [fully-connected] "" connection: guid=1139410826453420400 ip=192.168.1.4 steam-id=76561197968989085 access= username="Sal" connection-type="UDPRakNet"
# LOG  : Network     , 1732903874607> 21,692,562> Disconnected player "Sal" 76561197968989085
# LOG  : General     , 1732956822901> 7,128,548> PlayerDeath { "player": "Sal", "hours": 0, "zkills": 0, "position": { "x": 10897, "y": 10126, "z": 0 }}
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    LOGIN, LOGOUT = '> ConnectionManager: [fully-connected]', '> Disconnected player'
    LOGIN_FILTER, LOGOUT_FILTER = msgftr.DataStrContains(LOGIN), msgftr.DataStrContains(LOGOUT)
    DEATH_FILTER = msgftr.DataStrContains('> PlayerDeath { "player"')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            CONSOLE_OUTPUT_FILTER,
            msgftr.Or(_PlayerEventSubscriber.LOGIN_FILTER,
                      _PlayerEventSubscriber.LOGOUT_FILTER,
                      _PlayerEventSubscriber.DEATH_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            steamid = util.lchop(message.data(), 'steam-id=')
            steamid = util.rchop(steamid, 'access=')
            steamid = util.rchop(steamid, '(owner=')
            name = util.lchop(message.data(), 'username="')
            name = util.rchop(name, '" connection-type=')
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name, steamid)
            return None
        if _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            parts = util.lchop(message.data(), _PlayerEventSubscriber.LOGOUT).split(' ')
            steamid, name = parts[-1], ' '.join(parts[:-1])
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name[1:-1], steamid)
            return None
        if _PlayerEventSubscriber.DEATH_FILTER.accepts(message):
            data = objconv.json_to_dict(util.lchop(message.data(), 'PlayerDeath'))
            name = util.get('player', data)
            if name:
                text = 'survived ' + str(util.get('hours', data, '?')) + ' hours'
                text += ', killed ' + str(util.get('zkills', data, '?')) + ' zombies'
                text += ', died at '
                position = util.get('position', data)
                text += str(util.get('x', position, '?')) + 'x '
                text += str(util.get('y', position, '?')) + 'y '
                text += str(util.get('z', position, '?')) + 'z'
                playerstore.PlayersSubscriber.event_death(self._mailer, self, name, text)
            return None
        return None


# New message 'ChatMessage{chat=General, author='Sal', text='Helo Everyone'}' was sent members of chat '0'
class _PlayerChatSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.DataStrContains(_CHAT_KEY_STRING)))
        self._mailer = mailer

    def handle(self, message):
        name = util.lchop(message.data(), 'author=')
        name = util.rchop(name, ', text=')
        text = util.lchop(message.data(), ', text=')
        text = util.rchop(text, '}\' was sent members of chat')
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
