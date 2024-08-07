import os
import sys
import shutil
from yarl import URL
from core.util import util
from core.context import contextsvc
from core.http import httprsc
from core.system import system

_SJ_DIR = '/serverjockey'
_SCHEME = 'test'
_BASEURL = _SCHEME + '://'


class TestContext:

    def __init__(self):
        self._syssvc, self._resources = None, None
        home, cwd = '/tmp/sjgmstest', os.getcwd()
        if os.path.isdir(home):
            shutil.rmtree(home)
        template = util.rchop(cwd, _SJ_DIR) + _SJ_DIR + '/test/instances'
        shutil.copytree(template, home)
        tempdir = home + '/.tmp'
        os.makedirs(tempdir)
        self._context = contextsvc.Context(
            debug=True, trace=False, home=home, tempdir=tempdir,
            stime=None, secret='token', showtoken=False,
            scheme=_SCHEME, env=os.environ.copy(), python=sys.executable,
            logfile=None, dbfile=None, noupnp=True, host=None, port=None)

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
