import typing
import asyncio
import shlex
from rcon.source import rcon
# ALLOW const.* util.* msg.* context.* http.* system.* proc.*
from core.util import util
from core.msg import msgabc, msgftr, msgext
from core.http import httpabc


class RconHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_post(self, resource, data):
        cmdline = util.get('line', data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        response = await RconService.request(self._mailer, self, str(cmdline))
        return response if response else httpabc.ResponseBody.NO_CONTENT


class RconService(msgabc.AbcSubscriber):
    CONFIG = 'RconService.Config'
    REQUEST = 'RconService.Request'
    RESPONSE = 'RconService.Response'
    EXCEPTION = 'RconService.Exception'
    OUTPUT = 'RconService.Output'
    FILTER_OUTPUT = msgftr.NameIs(OUTPUT)

    @staticmethod
    async def request(mailer: msgabc.MulticastMailer, source: typing.Any, cmdline: str) -> typing.Any:
        response = await msgext.SynchronousMessenger(mailer).request(source, RconService.REQUEST, cmdline)
        return response.data()

    @staticmethod
    def set_config(mailer: msgabc.Mailer, source: typing.Any, port: int, password: str):
        mailer.post(source, RconService.CONFIG, {'port': port, 'password': password})

    def __init__(self, mailer: msgabc.Mailer, out_prefix: str = '', enforce_id: bool = True):
        super().__init__(msgftr.NameIn((RconService.CONFIG, RconService.REQUEST)))
        self._mailer = mailer
        self._out_prefix, self._enforce_id = out_prefix, enforce_id
        self._port, self._password = None, None

    async def handle(self, message):
        if message.name() is RconService.CONFIG:
            config = message.data()
            self._port, self._password = util.get('port', config), util.get('password', config)
            return None
        try:
            if not self._port or not self._password:
                raise Exception('No rcon config set.')
            cmdline = message.data()
            if not cmdline:
                raise Exception('No rcon cmdline provided.')
            cmd = shlex.split(cmdline, posix=False)
            coro = rcon(cmd[0], *cmd[1:], host='localhost', port=self._port,
                        passwd=self._password, enforce_id=self._enforce_id)
            result = await asyncio.wait_for(coro, 6.0)
            if result:
                for line in result.strip().split('\n'):
                    self._mailer.post(self, RconService.OUTPUT, self._out_prefix + line)
            self._mailer.post(self, RconService.RESPONSE, result, message)
        except Exception as e:
            self._mailer.post(self, RconService.EXCEPTION, e, message)
        return None
