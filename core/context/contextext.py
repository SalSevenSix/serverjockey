# ALLOW const.* util.* msg*.* contextsvc.*
from core.util import util, io, objconv, funcutil
from core.context import contextsvc


class RootUrl:

    def __init__(self, context: contextsvc.Context):
        self._context = context

    def build(self, fallback_host: str = 'localhost') -> str:
        scheme = self._context.config('scheme')
        host = self._context.config('host')
        if not host:
            host = fallback_host
        port = self._context.config('port')
        return util.build_url(scheme, host, port)


class ClientFile:

    def __init__(self, context: contextsvc.Context, clientfile: str):
        self._context, self._clientfile = context, clientfile

    def path(self):
        return self._clientfile

    async def write(self):
        if not self._clientfile:
            return
        data = objconv.obj_to_json({
            'SERVER_URL': RootUrl(self._context).build(),
            'SERVER_TOKEN': self._context.config('secret')
        })
        await io.write_file(self._clientfile, data)

    async def delete(self):
        await funcutil.silently_call(io.delete_file(self._clientfile))
