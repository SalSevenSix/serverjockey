from __future__ import annotations
import asyncio
import typing
# ALLOW util.* msg*.*
from core.util import util, funcutil
from core.msg import msgabc, msgsvc


class Context(msgabc.MulticastMailer):

    def __init__(self, configuration: dict):
        self._parent: typing.Optional[Context] = None
        self._children: typing.List[Context] = []
        self._configuration = configuration.copy() if configuration else {}
        self._mailer = msgsvc.TaskMulticastMailer()

    def start(self) -> asyncio.Task:
        return self._mailer.start()

    def create_subcontext(self, configuration: dict) -> Context:
        subcontext = Context(configuration)
        subcontext._parent = self
        self._children.append(subcontext)
        return subcontext

    async def destroy_subcontext(self, subcontext: Context):
        await subcontext.shutdown()
        self._children.remove(subcontext)

    def root(self):
        if self._parent:
            return self._parent.root()
        return self

    def subcontexts(self) -> typing.Collection[Context]:
        return tuple(self._children)

    def config(self, key: str = None) -> typing.Any:
        if key is None:
            return self._configuration.copy()
        value = util.get(key, self._configuration)
        if value is not None or self._parent is None:
            return value
        return self._parent.config(key)

    def set_config(self, key: str, value: typing.Any):
        self._configuration[key] = value

    def env(self, key: str = None) -> dict | str | None:
        env = self.config('env')
        if key is None:
            return env.copy() if env else {}
        return util.get(key, env)

    def is_debug(self) -> bool:
        return self.config('debug') or self.is_trace()

    def is_trace(self) -> bool:
        return self.config('trace')

    def register(self, subscriber: msgabc.Subscriber) -> msgabc.Mailer:
        return self._mailer.register(subscriber)

    def post(self, *vargs) -> bool:
        return self._mailer.post(*vargs)

    async def shutdown(self):
        for subcontext in self.subcontexts():
            await self.destroy_subcontext(subcontext)
        await funcutil.silently_cleanup(self._mailer)

    def asdict(self):
        return self._configuration.copy()
