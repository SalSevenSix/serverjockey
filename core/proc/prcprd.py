import logging
import typing
from asyncio import streams
# ALLOW util.* msg.* context.* proc.prcenc
from core.util import funcutil
from core.msg import msgabc, msgext
from core.proc import prcenc


class PipeOutLineProducer(msgabc.Producer):

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any, name: str,
                 pipe: streams.StreamReader, decoder: prcenc.LineDecoder = prcenc.DefaultLineDecoder()):
        self._source = source
        self._name = name
        self._pipe = pipe
        self._decoder = decoder
        self._publisher = msgext.Publisher(mailer, self)

    async def close(self):
        await funcutil.silently_cleanup(self._pipe)
        await funcutil.silently_cleanup(self._publisher)

    async def next_message(self):
        # noinspection PyBroadException
        try:
            line = await self._pipe.readline()
            if line is None or line == b'':
                logging.debug('EOF read from PipeOut: ' + repr(self._pipe))
                return None
            return msgabc.Message(self._source, self._name, self._decoder.decode(line))
        except Exception as e:
            logging.error('Pipe read line failed: ' + repr(e))
        return None