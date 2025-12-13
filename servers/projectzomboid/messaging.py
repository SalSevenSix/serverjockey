# ALLOW core.*
from core.util import util, dtutil, sysutil
from core.msg import msgabc, msglog, msgftr
from core.msgc import mc
from core.context import contextsvc
from core.system import svrsvc
from core.proc import proch, jobh
from core.common import cachelock, playerstore, svrhelpers

SERVER_STARTED_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('*** SERVER STARTED ***'))
CONSOLE_LOG_FILTER = msgftr.Or(
    msgftr.And(
        mc.ServerProcess.FILTER_ALL_LINES,
        msgftr.Not(msgftr.Or(
            msgftr.DataStrContains('password', True),
            msgftr.DataStrContains('token', True),
            msgftr.DataStrContains('command entered via server console', True)))),
    jobh.JobProcess.FILTER_ALL_LINES, msglog.LogPublisher.LOG_FILTER, cachelock.FILTER_NOTIFICATIONS)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.Or(msgftr.DataStrStartsWith('ERROR:'), msgftr.DataStrStartsWith('SEVERE:')))
CONSOLE_OUTPUT_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.Not(msgftr.DataStrContains('ChatMessage{chat=General')))
SERVER_PORT, SERVER_RESTART_REQUIRED = 'messaging.SERVER_PORT', 'messaging.RESTART_REQUIRED'
SERVER_PORT_FILTER = msgftr.NameIs(SERVER_PORT)
SERVER_RESTART_REQUIRED_FILTER = msgftr.NameIs(SERVER_RESTART_REQUIRED)


async def initialise(context: contextsvc.Context):
    svrhelpers.MessagingInitHelper(context).init_state().init_players()
    context.register(_ServerDetailsSubscriber(context, await sysutil.public_ip()))
    context.register(_PlayerEventSubscriber(context))
    context.register(_PlayerChatSubscriber(context))
    context.register(_ProvideAdminPasswordSubscriber(context, context.config('secret')))


# LOG  : General   b41 > version=41.78.16 demo=false
# LOG  : General   b42 > version=42.13.0 02...76f 2025-12-11 08:13:47 (ZB) demo=false
# LOG  : Network   b41 > [09-10-25 13:26:13.462] > ZNet: Public IP: 14.237.58.218
# LOG  : Network   b41 > Clients should use 16261 port for connections
# LOG  : General   mod > IngameTime 1993-07-09 18:00
class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches(r'.*> version=(.*?) .*')
    INGAMETIME_FILTER = msgftr.DataMatches(r'.*> IngameTime (.*?)$')

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.Or(
            SERVER_RESTART_REQUIRED_FILTER, SERVER_PORT_FILTER,
            msgftr.And(
                CONSOLE_OUTPUT_FILTER,
                msgftr.Or(_ServerDetailsSubscriber.INGAMETIME_FILTER, _ServerDetailsSubscriber.VERSION_FILTER))))
        self._mailer, self._public_ip, self._port = mailer, public_ip, '16261'

    def handle(self, message):
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            ingametime = _ServerDetailsSubscriber.INGAMETIME_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ingametime=ingametime))
        elif SERVER_RESTART_REQUIRED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(restart=dtutil.to_millis(message.created())))
        elif SERVER_PORT_FILTER.accepts(message):
            self._port = message.data()
        elif _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            version = _ServerDetailsSubscriber.VERSION_FILTER.find_one(message.data())
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(
                version=version, ip=self._public_ip, port=self._port))
        return None


# LOG  : Network   b41 > ConnectionManager: [fully-connected] "" connection: guid=1139410826453420400 ip=192.168.1.4 ste
#   am-id=76561197968989085 access= username="Sal" connection-type="UDPRakNet"
# b42   [12-12-25 18:31:34.628] 76561197968989085 "Apollo" fully connected (10856,9894,0).
# LOG  : Network   b41 > Disconnected player "Sal" 76561197968989085
# b42   [12-12-25 18:33:42.901] 76561197968989085 "Apollo" disconnected player (10856,9894,0).
# LOG  : General   mod > PlayerDeath { "player": "Sal", "hours": 0, "zkills": 0, "position": { "x": 10897, "y": 10126, "
#   z": 0 }}
# b42   [13-12-25 07:51:08.007] user Truffle Pigg died at (3104,6147,0) (non pvp).
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    LOGIN_FILTER = msgftr.DataMatches(r'^\[.*\] (.*?) "(.*?)" fully connected \(.*\)\.$')
    LOGOUT_FILTER = msgftr.DataMatches(r'^\[.*\] (.*?) "(.*?)" disconnected player \(.*\)\.$')
    DEATH_FILTER = msgftr.DataMatches(r'^\[.*\] user (.*?) died at \((.*?)\).*')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            CONSOLE_OUTPUT_FILTER,
            msgftr.Or(_PlayerEventSubscriber.LOGIN_FILTER,
                      _PlayerEventSubscriber.LOGOUT_FILTER,
                      _PlayerEventSubscriber.DEATH_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            steamid, name = util.fill(_PlayerEventSubscriber.LOGIN_FILTER.find_all(message.data()), 2)
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name, steamid)
        elif _PlayerEventSubscriber.LOGOUT_FILTER.accepts(message):
            steamid, name = util.fill(_PlayerEventSubscriber.LOGOUT_FILTER.find_all(message.data()), 2)
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name, steamid)
        elif _PlayerEventSubscriber.DEATH_FILTER.accepts(message):
            name, position = util.fill(_PlayerEventSubscriber.DEATH_FILTER.find_all(message.data()), 2)
            if name:
                name, text = name.strip(), 'died at ' + position if position else None
                playerstore.PlayersSubscriber.event_death(self._mailer, self, name, text)
        return None


# New message 'ChatMessage{chat=General, author='Sal', text='Helo Everyone'}' was sent members of chat '0'
# [...][info] Message ChatMessage{chat=General, author='Apollo', text='hello from game'} sent to chat (id = 0) members.
class _PlayerChatSubscriber(msgabc.AbcSubscriber):
    CHAT_FILTER = msgftr.DataMatches(
        r"^\[.*\]\[info\] Message ChatMessage\{chat=General, author='(.*?)', text='(.*?)'\} sent to chat.*")

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, _PlayerChatSubscriber.CHAT_FILTER))
        self._mailer = mailer

    def handle(self, message):
        name, text = util.fill(_PlayerChatSubscriber.CHAT_FILTER.find_all(message.data()), 2)
        playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
        return None


class _ProvideAdminPasswordSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer, pwd: str):
        super().__init__(msgftr.And(
            CONSOLE_OUTPUT_FILTER,
            msgftr.Or(msgftr.DataStrContains('Enter new administrator password'),
                      msgftr.DataStrContains('Confirm the password'))))
        self._mailer, self._pwd = mailer, pwd

    async def handle(self, message):
        await proch.PipeInLineService.request(self._mailer, self, self._pwd, force=True)
        return None
