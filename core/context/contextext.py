from core.util import util, io
from core.context import contextsvc


class ClientFile:
    WRITTEN = 'ClientFile.Written'

    def __init__(self, context: contextsvc.Context, clientfile: str):
        self._context = context
        self._clientfile = clientfile

    def path(self):
        return self._clientfile

    async def write(self):
        scheme = self._context.config('scheme')
        host = self._context.config('host')
        host = host if host else 'localhost'
        port = self._context.config('port')
        data = util.obj_to_json({
            'SERVER_URL': util.build_url(scheme, host, port),
            'SERVER_TOKEN': self._context.config('secret')
        })
        await io.write_file(self._clientfile, data)
        self._context.post(self, ClientFile.WRITTEN, self._clientfile)

    # noinspection PyBroadException
    async def delete(self):
        try:
            await io.delete_file(self._clientfile)
        except Exception:
            pass
