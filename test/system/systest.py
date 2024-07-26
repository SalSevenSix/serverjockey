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
        self._context = contextsvc.Context(dict(
            home=home, logfile=None, tempdir=tempdir, host=None, port=None, showtoken=False,
            noupnp=True, dbfile=None, debug=True, trace=False, secret='token', python=sys.executable,
            stime=None, scheme=_SCHEME, env=os.environ.copy()))

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
