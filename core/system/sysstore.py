import typing
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
# TODO ALLOW ???
from core.msg import msgabc
from core.context import contextsvc
from core.system import system
from core.store import storeabc, storesvc


def initialise(context: contextsvc.Context, source: typing.Any):
    context.register(storesvc.StoreService(context))
    context.post(source, storesvc.StoreService.INITIALISE)
    context.register(_SystemRouting(context))


class _SystemRouting(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(system.SystemService.SERVER_FILTER)
        self._mailer = mailer

    async def handle(self, message):
        source, name, data = message.source(), message.name(), message.data()
        if name is system.SystemService.SERVER_INITIALISED:
            storeabc.execute(self._mailer, source, _InsertInstance(data))
            return None
        if name is system.SystemService.SERVER_DELETED:
            storeabc.execute(self._mailer, source, _DeleteInstance(data))
            return None
        return None


class _InsertInstance(storeabc.Transaction):

    def __init__(self, subcontext):
        self._subcontext = subcontext

    async def execute(self, session: AsyncSession) -> typing.Any:
        name, module = self._subcontext.config('identity'), self._subcontext.config('module')
        statement = select(storeabc.Instance).where(storeabc.Instance.name == str(name))
        results = await session.scalars(statement)
        if not results.first():
            session.add(storeabc.Instance(name=name, module=module))
        return None


class _DeleteInstance(storeabc.Transaction):

    def __init__(self, subcontext):
        self._subcontext = subcontext

    async def execute(self, session: AsyncSession) -> typing.Any:
        statement = select(storeabc.Instance).where(storeabc.Instance.name == str(self._subcontext.config('identity')))
        results = await session.scalars(statement)
        instance = results.first()
        if instance:
            await session.delete(instance)
        return None
