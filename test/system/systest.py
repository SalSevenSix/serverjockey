import os
import sys
from yarl import URL
from core.context import contextsvc
from core.http import httprsc
from core.system import system


class TestContext:

    def __init__(self):
        self._syssvc, self._resources = None, None
        env = os.environ.copy()
        self._context = contextsvc.Context(
            debug=False, home=env['HOME'] + '/serverjockey', secret='test', showtoken=False,
            scheme='http', sslcert=None, sslkey=None, env=env,
            python=sys.executable, logfile=None, clientfile=None, host=None, port=None)

    async def initialise(self):
        if self._resources:
            return
        self._context.start()
        self._syssvc = system.SystemService(self._context)
        await self._syssvc.initialise()
        self._resources = self._syssvc.resources()

    def context(self):
        return self._context

    def resources(self):
        return self._resources


_BASEURL = 'http://localhost:6164'
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