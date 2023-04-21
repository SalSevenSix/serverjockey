from __future__ import annotations
import asyncio
import typing
# ALLOW util.* msg.*
from core.util import util, funcutil
from core.msg import msgabc, msgsvc


class Context(msgabc.MulticastMailer):

    def __init__(self, **configuration: typing.Any):
        self._parent: typing.Optional[Context] = None
        self._children: typing.List[Context] = []
        self._configuration = configuration.copy() if configuration else {}
        self._mailer = msgsvc.TaskMulticastMailer()

    def start(self) -> asyncio.Task:
        return self._mailer.start()

    def create_subcontext(self, **configuration: typing.Any) -> Context:
        subcontext = Context(**configuration)
        subcontext._parent = self
        self._children.append(subcontext)
        return subcontext

    async def destroy_subcontext(self, subcontext: Context):
        await subcontext.shutdown()
        self._children.remove(subcontext)

    def subcontexts(self) -> typing.Collection[Context]:
        return tuple(self._children)

    def config(self, key: str) -> typing.Any:
        value = util.get(key, self._configuration)
        if value is not None or self._parent is None:
            return value
        return self._parent.config(key)

    def is_debug(self) -> bool:
        return self.config('debug')

    def register(self, subscriber: msgabc.Subscriber) -> asyncio.Task:
        return self._mailer.register(subscriber)

    def post(self, *vargs) -> bool:
        return self._mailer.post(*vargs)

    async def shutdown(self):
        for subcontext in iter(self.subcontexts()):
            await self.destroy_subcontext(subcontext)
        await funcutil.silently_cleanup(self._mailer)

    def asdict(self):
        return self._configuration.copy()
