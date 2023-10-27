import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio.session import AsyncSession
# TODO ALLOW ???
from core.util import io, funcutil, sysutil, objconv
from core.msg import msgabc, msgftr
from core.context import contextsvc
from core.store import storeabc


class StoreService(msgabc.AbcSubscriber):
    INITIALISE = 'StoreService.Initialise'

    def __init__(self, context: contextsvc.Context):
        super().__init__(msgftr.Or(
            msgftr.NameIn((StoreService.INITIALISE, storeabc.TRANSACTION)),
            msgftr.IsStop()))
        self._context = context
        self._engine: AsyncEngine | None = None
        self._session: AsyncSession | None = None

    async def handle(self, message):
        if message is msgabc.STOP:
            return await self._close()
        name = message.name()
        if name is StoreService.INITIALISE:
            return await self._initialise()
        if not self._session:
            return False
        if name is storeabc.TRANSACTION:
            await self._transaction(message)
        return None

    async def _initialise(self) -> bool | None:
        create_database, database_path = False, self._context.config('dbfile')
        if not database_path:
            return False
        try:
            create_database = not await io.file_exists(database_path)
            self._engine = create_async_engine('sqlite+aiosqlite:///' + database_path)
            if create_database:
                async with self._engine.begin() as connection:
                    await connection.run_sync(storeabc.Base.metadata.create_all)
                logging.debug('Created database: ' + database_path)
            session_maker = async_sessionmaker(self._engine)
            self._session = session_maker()
            if create_database:
                async with self._session.begin():
                    self._session.add(storeabc.SystemEvent(
                        at=datetime.now(), name='SCHEMA',
                        details=objconv.obj_to_json(sysutil.system_version_dict())))
            return None
        except Exception as e:
            logging.error('Error initialising database: ' + repr(e))
            await self._close()
            if create_database:
                await funcutil.silently_call(io.delete_file(database_path))
        return False

    async def _transaction(self, message):
        transaction: storeabc.Transaction = message.data()
        result = None
        try:
            async with self._session.begin():
                result = await transaction.execute(self._session)
        except Exception as e:
            result = e
            logging.error('Transation error: ' + repr(e))
        finally:
            self._context.post(message.source(), storeabc.TRANSACTION_RESPONSE, result, message)

    async def _close(self) -> bool:
        await funcutil.silently_cleanup(self._session)
        await funcutil.silently_cleanup(self._engine)
        self._engine, self._session = None, None
        return True
