import os
import ssl
# ALLOW util.* msg*.* context.* http.*
from core.context import contextsvc
from core.http import httpabc, httpcnt
from core.util import gc, util, io, funcutil, shellutil, idutil

_CERT_FILE, _KEY_FILE = '/serverjockey.crt', '/serverjockey.key'


def sync_get_scheme(home: str) -> str:
    return gc.HTTPS if os.path.isfile(home + _CERT_FILE) and os.path.isfile(home + _KEY_FILE) else gc.HTTP


class SslTool:

    def __init__(self, context: contextsvc.Context):
        self._context, self._scheme = context, context.config('scheme')
        home_dir, self._tempdir = context.config('home'), context.config('tempdir')
        self._sslcert, self._sslkey = home_dir + _CERT_FILE, home_dir + _KEY_FILE

    def ssl_context(self) -> ssl.SSLContext | None:
        if not self.is_active():
            return None
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(self._sslcert, self._sslkey)
        return ssl_context

    def is_active(self):
        return self._scheme == gc.HTTPS

    async def is_enabled(self):
        return await _files_exist(self._sslcert, self._sslkey)

    async def enable(self):
        working_dir = self._tempdir + '/' + idutil.generate_id()
        try:
            await io.create_directory(working_dir)
            sslcert, sslkey = working_dir + _CERT_FILE, working_dir + _KEY_FILE
            script = 'openssl req -newkey rsa:4096 -x509 -sha512 -days 365 -nodes'
            script += ' -out ' + sslcert + ' -keyout ' + sslkey
            script += ' -subj "/CN=serverjockey"'
            await shellutil.run_script(script)
            if not await _files_exist(sslcert, sslkey):
                raise Exception('SslTool.enable() failed to create cert and key files')
            await self.disable()
            await io.move_path(sslcert, self._sslcert)
            await io.move_path(sslkey, self._sslkey)
            await io.chmod(self._sslcert, 0o600)
            await io.chmod(self._sslkey, 0o600)
        finally:
            await funcutil.silently_call(io.delete_directory(working_dir))

    async def disable(self):
        await io.delete_file(self._sslcert)
        await io.delete_file(self._sslkey)


class SslHandler(httpabc.GetHandler, httpabc.PostHandler):

    def __init__(self, context: contextsvc.Context):
        self._context = context

    async def handle_get(self, resource, data):
        if not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        tool = SslTool(self._context)
        return {'active': tool.is_active(), 'enabled': await tool.is_enabled()}

    async def handle_post(self, resource, data):
        tool = SslTool(self._context)
        if util.get('enabled', data):
            await tool.enable()
        else:
            await tool.disable()
        return httpabc.ResponseBody.NO_CONTENT


async def _files_exist(path_a: str, path_b: str) -> bool:
    has_a = await io.file_exists(path_a)
    has_b = await io.file_exists(path_b)
    return has_a and has_b
