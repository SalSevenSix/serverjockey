import logging
import typing
from asyncio import streams
from core.util import funcutil, io, pkg
from core.msg import msgabc, msgext


async def unpack_wrapper(path: str):
    filename = path + '/wrapper.py'
    data = await pkg.pkg_load('core.proc', 'wrapper.py')
    await io.write_file(filename, data)
    return filename


class PipeOutLineProducer(msgabc.Producer):

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any, name: str, pipe: streams.StreamReader):
        self._source = source
        self._name = name
        self._pipe = pipe
        self._publisher = msgext.Publisher(mailer, self)

    async def close(self):
        await funcutil.silently_cleanup(self._pipe)
        await funcutil.silently_cleanup(self._publisher)

    async def next_message(self):
        line = None
        # noinspection PyBroadException
        try:
            line = await self._pipe.readline()
        except Exception:
            pass
        if line is None or line == b'':
            logging.debug('EOF read from PipeOut: ' + repr(self._pipe))
            return None
        return msgabc.Message(self._source, self._name, line.decode().strip())
