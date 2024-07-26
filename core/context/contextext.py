# ALLOW util.* msg*.* contextsvc.*
from core.util import util, io, objconv, funcutil
from core.context import contextsvc


class RootUrl:

    def __init__(self, context: contextsvc.Context):
        self._context = context

    def build(self, fallback_host: str = 'localhost') -> str:
        scheme = self._context.config('scheme')
        host = self._context.config('host')
        host = host[0] if host else fallback_host
        port = self._context.config('port')
        return util.build_url(scheme, host, port)


class ClientFile:

    def __init__(self, context: contextsvc.Context, tokenfile: bool = False):
        self._context, home = context, context.config('home')
        self._clientfile = util.full_path(home, 'serverjockey-client.json')
        self._tokenfile = util.full_path(home, 'serverjockey-token.text') if tokenfile else None

    def path(self):
        return self._clientfile

    async def write(self):
        if not self._clientfile:
            return
        secret = self._context.config('secret')
        data = objconv.obj_to_json({
            'SERVER_URL': RootUrl(self._context).build(),
            'SERVER_TOKEN': secret
        })
        await io.write_file(self._clientfile, data)
        if self._tokenfile:
            await io.write_file(self._tokenfile, secret)

    async def delete(self):
        await funcutil.silently_call(io.delete_file(self._clientfile))
        if self._tokenfile:
            await funcutil.silently_call(io.delete_file(self._tokenfile))
