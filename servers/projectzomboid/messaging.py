import asyncio
from core.context import contextsvc
from core.util import util
from core.msg import msgabc, msgftr
from core.proc import proch, prcext
from core.system import svrsvc


def initialise(context: contextsvc.Context):
    context.register(prcext.ServerStateSubscriber(context))
    context.register(_ServerDetailsSubscriber(context))
    context.register(_RestartSubscriber(context))
    context.register(_ModUpdatedSubscriber(context))
    context.register(_ProvideAdminPasswordSubscriber(context, context.config('secret')))


class _ConsoleLogFilter(msgabc.Filter):

    def accepts(self, message):
        if not (proch.ServerProcess.FILTER_STDOUT_LINE.accepts(message)
                or proch.ServerProcess.FILTER_STDERR_LINE.accepts(message)):
            return False
        value = message.data().lower()
        if value.find('password') != -1:
            return False
        if value.find('token') != -1:
            return False
        if value.find('command entered via server console') != -1:
            return False
        return True


CONSOLE_LOG_FILTER = _ConsoleLogFilter()
NOT_CHAT_MESSAGE = msgftr.Not(msgftr.DataStrContains("New message 'ChatMessage{chat=General"))
SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataStrContains('*** SERVER STARTED ***'))
SERVER_RESTART_REQUIRED = 'messaging.RESTART_REQUIRED'
SERVER_RESTART_REQUIRED_FILTER = msgftr.NameIs(SERVER_RESTART_REQUIRED)


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION = '> version='
    VERSION_FILTER = msgftr.DataStrContains(VERSION)
    IP = 'Public IP:'
    IP_FILTER = msgftr.DataStrContains(IP)
    PORT = '> Clients should use'
    PORT_FILTER = msgftr.DataStrContains(PORT)
    STEAMID = 'Server Steam ID'
    STEAMID_FILTER = msgftr.DataStrContains(STEAMID)
    INGAMETIME = '> IngameTime'
    INGAMETIME_FILTER = msgftr.DataStrContains(INGAMETIME)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            SERVER_RESTART_REQUIRED_FILTER,
            msgftr.And(
                proch.ServerProcess.FILTER_STDOUT_LINE,
                NOT_CHAT_MESSAGE,
                msgftr.Or(_ServerDetailsSubscriber.INGAMETIME_FILTER,
                          _ServerDetailsSubscriber.VERSION_FILTER,
                          _ServerDetailsSubscriber.IP_FILTER,
                          _ServerDetailsSubscriber.PORT_FILTER,
                          _ServerDetailsSubscriber.STEAMID_FILTER))))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.INGAMETIME)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ingametime': value})
            return None
        if SERVER_RESTART_REQUIRED_FILTER.accepts(message):
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'restart': util.now_millis()})
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
        if _ServerDetailsSubscriber.STEAMID_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.STEAMID)
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'steamid': int(value)})
        return None


class _ModUpdatedSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            NOT_CHAT_MESSAGE,
            msgftr.DataStrContains('[ModzCheck] Mod update required')))
        self._mailer = mailer

    def handle(self, message):
        self._mailer.post(self, SERVER_RESTART_REQUIRED)
        return None


class _RestartSubscriber(msgabc.AbcSubscriber):
    WAIT = '_ModUpdateRestartSubscriber.Wait'
    WAIT_FILTER = msgftr.NameIs(WAIT)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            SERVER_RESTART_REQUIRED_FILTER,
            _RestartSubscriber.WAIT_FILTER,
            proch.ServerProcess.FILTER_STATE_DOWN,
            msgftr.IsStop()))
        self._mailer = mailer
        self._second_message = False
        self._initiated = 0

    async def handle(self, message):
        if message is msgabc.STOP:
            self._initiated, self._second_message = 0, False
            return True
        if proch.ServerProcess.FILTER_STATE_DOWN.accepts(message):
            self._initiated, self._second_message = 0, False
            return None
        if self._initiated == 0 and SERVER_RESTART_REQUIRED_FILTER.accepts(message):
            self._initiated, self._second_message = util.now_millis(), False
            await proch.PipeInLineService.request(
                self._mailer, self,
                'servermsg "Mod updated. Server restart in 5 minutes. Please find a safe place and logout."')
            self._mailer.post(self, _RestartSubscriber.WAIT)
            return None
        if self._initiated > 0 and _RestartSubscriber.WAIT_FILTER.accepts(message):
            waited = util.now_millis() - self._initiated
            if waited > 300000:  # 5 minutes
                self._initiated, self._second_message = 0, False
                svrsvc.ServerService.signal_restart(self._mailer, self)
                return None
            if not self._second_message and waited > 240000:  # 4 minutes
                self._second_message = True
                await proch.PipeInLineService.request(
                    self._mailer, self,
                    'servermsg "Mod updated. Server restart in 1 minute. Please find a safe place and logout."')
                self._mailer.post(self, _RestartSubscriber.WAIT)
                return None
            await asyncio.sleep(1)
            self._mailer.post(self, _RestartSubscriber.WAIT)
        return None


class _ProvideAdminPasswordSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer, pwd: str):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            NOT_CHAT_MESSAGE,
            msgftr.Or(msgftr.DataStrContains('Enter new administrator password'),
                      msgftr.DataStrContains('Confirm the password'))))
        self._mailer = mailer
        self._pwd = pwd

    async def handle(self, message):
        await proch.PipeInLineService.request(self._mailer, self, self._pwd, force=True)
        return None
