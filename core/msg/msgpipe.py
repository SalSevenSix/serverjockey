import logging
import typing
from asyncio import streams
# ALLOW util.* msg*.* context.*
from core.util import funcutil, io, linenc
from core.msg import msgabc, msgext


class PipeOutLineProducer(msgabc.Producer):

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any, name: str,
                 pipe: streams.StreamReader, decoder: linenc.LineDecoder = linenc.DefaultLineDecoder()):
        self._source, self._name, self._pipe, self._decoder = source, name, pipe, decoder
        self._publisher = msgext.Publisher(mailer, self)

    async def close(self):
        await funcutil.silently_cleanup(self._pipe)
        await funcutil.silently_cleanup(self._publisher)

    async def next_message(self):
        try:
            line = await self._pipe.readline()
            if io.end_of_stream(line):
                logging.debug('EOF read from PipeOut: %s', repr(self._pipe))
                return None
            return msgabc.Message(self._source, self._name, self._decoder.decode(line))
        except Exception as e:
            logging.error('Pipe read line failed: %s', repr(e))
        return None
