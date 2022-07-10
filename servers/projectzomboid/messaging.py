from core.context import contextsvc
from core.util import util
from core.msg import msgabc, msgftr
from core.proc import proch, prcext
from core.system import svrsvc


class Messaging:

    def __init__(self, context: contextsvc.Context):
        self._context = context

    def initialise(self):
        self._context.register(prcext.ServerStateSubscriber(self._context))
        self._context.register(_ServerDetailsSubscriber(self._context))
        self._context.register(_ProvideAdminPasswordSubscriber(self._context, self._context.config('secret')))


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


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION = 'versionNumber='
    VERSION_FILTER = msgftr.DataStrContains(VERSION)
    PORT = 'server is listening on port'
    PORT_FILTER = msgftr.DataStrContains(PORT)
    STEAMID = 'Server Steam ID'
    STEAMID_FILTER = msgftr.DataStrContains(STEAMID)
    INGAMETIME = '> IngameTime'
    INGAMETIME_FILTER = msgftr.DataStrContains(INGAMETIME)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_ServerDetailsSubscriber.INGAMETIME_FILTER,
                      _ServerDetailsSubscriber.VERSION_FILTER,
                      _ServerDetailsSubscriber.PORT_FILTER,
                      _ServerDetailsSubscriber.STEAMID_FILTER)))
        self._mailer = mailer

    # TODO grab IP
    def handle(self, message):
        data = None
        if _ServerDetailsSubscriber.INGAMETIME_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.INGAMETIME)
            data = {'ingametime': value}
        elif _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.VERSION)
            value = util.right_chop_and_strip(value, 'demo=')
            data = {'version': value}
        elif _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.PORT)
            data = {'port': int(value)}
        elif _ServerDetailsSubscriber.STEAMID_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _ServerDetailsSubscriber.STEAMID)
            data = {'steamid': int(value)}
        if data:
            svrsvc.ServerStatus.notify_details(self._mailer, self, data)
        return None


class _ProvideAdminPasswordSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.MulticastMailer, pwd: str):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(msgftr.DataStrContains('Enter new administrator password'),
                      msgftr.DataStrContains('Confirm the password'))))
        self._mailer = mailer
        self._pwd = pwd

    async def handle(self, message):
        await proch.PipeInLineService.request(self._mailer, self, self._pwd, force=True)
        return None
