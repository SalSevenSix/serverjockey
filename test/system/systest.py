import os
import sys
from yarl import URL
from core.util import util
from core.context import contextsvc
from core.http import httprsc
from core.system import system

_SJ_DIR = '/serverjockey'
_BASEURL = 'test://'


class TestContext:

    def __init__(self):
        cwd, self._syssvc, self._resources = os.getcwd(), None, None
        home = util.right_chop_and_strip(cwd, _SJ_DIR) + _SJ_DIR + '/test/instances'
        self._context = contextsvc.Context(
            debug=False, trace=False, home=home, tmpdir='/tmp', secret='token', showtoken=False,
            scheme='test', sslcert=None, sslkey=None, env=os.environ.copy(),
            python=sys.executable, logfile=None, clientfile=None, host=None, port=None)

    async def initialise(self):
        if self._resources:
            return
        self._context.start()
        self._syssvc = system.SystemService(self._context)
        await self._syssvc.initialise()
        self._resources = self._syssvc.resources()

    def resources(self):
        return self._resources


CONTEXT = TestContext()


async def _resources() -> httprsc.WebResource:
    await CONTEXT.initialise()
    return CONTEXT.resources()


async def get(path: str, secure: bool = True):
    resources = await _resources()
    return await resources.lookup(path).handle_get(URL(_BASEURL + path), secure)


async def post(path: str, body: dict = None):
    resources = await _resources()
    return await resources.lookup(path).handle_post(URL(_BASEURL + path), body if body else {})
