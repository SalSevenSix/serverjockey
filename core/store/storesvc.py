import logging
import typing
import time
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio.session import AsyncSession
# TODO ALLOW ???
from core.util import io, funcutil, sysutil, objconv
from core.msg import msgabc, msgftr
from core.context import contextsvc
from core.store import storeabc


async def _execute(session: AsyncSession, transaction: storeabc.Transaction) -> typing.Any:
    async with session.begin():
        return await transaction.execute(session)


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
            await self._close()
            return True
        name = message.name()
        if name is storeabc.TRANSACTION:
            await self._transaction(message)
            return None
        if name is StoreService.INITIALISE:
            database_path = self._context.config('dbfile')
            if not database_path:
                return True
            await self._initialise(database_path)
        return None

    async def _initialise(self, database_path: str):
        create_database = False
        try:
            create_database = not await io.file_exists(database_path)
            self._engine = create_async_engine('sqlite+aiosqlite:///' + database_path)
            if create_database:
                async with self._engine.begin() as connection:
                    await connection.run_sync(storeabc.Base.metadata.create_all)
                logging.debug('Created database: ' + database_path)
            session_maker = async_sessionmaker(self._engine)
            self._session = session_maker()
            if self._context.is_debug():
                aiosqlite_logger = logging.getLogger('aiosqlite')
                if aiosqlite_logger:
                    aiosqlite_logger.setLevel(logging.INFO)
            if create_database:
                await _execute(self._session, _CreateDatabaseDone())
            else:
                await _execute(self._session, _IntegrityChecks(self._context))
        except Exception as e:
            logging.error('Error initialising database: ' + repr(e))
            await self._close()
            if create_database:
                await funcutil.silently_call(io.delete_file(database_path))

    async def _transaction(self, message):
        result = None
        if not self._session:
            result = Exception('Session unavailable.')
            self._context.post(message.source(), storeabc.TRANSACTION_RESPONSE, result, message)
            return
        try:
            result = await _execute(self._session, message.data())
        except Exception as e:
            result = e
            logging.error('Transation error: ' + repr(e))
        finally:
            self._context.post(message.source(), storeabc.TRANSACTION_RESPONSE, result, message)

    async def _close(self):
        await funcutil.silently_cleanup(self._session)
        await funcutil.silently_cleanup(self._engine)
        self._engine, self._session = None, None


class _CreateDatabaseDone(storeabc.Transaction):

    async def execute(self, session: AsyncSession) -> typing.Any:
        session.add(storeabc.SystemEvent(
            at=time.time(), name='SCHEMA',
            details=objconv.obj_to_json(sysutil.system_version_dict())))
        return None


class _IntegrityChecks(storeabc.Transaction):

    def __init__(self, context: contextsvc.Context):
        self._stime = context.config('stime')

    async def execute(self, session: AsyncSession) -> typing.Any:
        corrections = 0
        emap = {'START': 'EXCEPTION', 'STARTING': 'EXCEPTION', 'STARTED': 'EXCEPTION',
                'STOPPING': 'STOPPED', 'MAINTENANCE': 'READY'}
        details = objconv.obj_to_json({'error': 'Event inserted by startup integrity check'})
        statement = select(storeabc.InstanceEvent)
        statement = statement.group_by(storeabc.InstanceEvent.instance_id)
        statement = statement.having(storeabc.InstanceEvent.name.in_(emap.keys()))
        statement = statement.having(func.max(storeabc.InstanceEvent.at))
        for event in await session.scalars(statement):
            corrections += 1
            event_at = self._stime if self._stime and self._stime > event.at else event.at + 1.0
            session.add(storeabc.InstanceEvent(
                at=event_at, instance_id=event.instance_id, name=emap[event.name], details=details))
        statement = select(storeabc.PlayerEvent)
        statement = statement.group_by(storeabc.PlayerEvent.player_id)
        statement = statement.having(storeabc.PlayerEvent.name == 'LOGIN')
        statement = statement.having(func.max(storeabc.PlayerEvent.at))
        for event in await session.scalars(statement):
            corrections += 1
            event_at = self._stime if self._stime and self._stime > event.at else event.at + 1.0
            session.add(storeabc.PlayerEvent(
                at=event_at, player_id=event.player_id, name='LOGOUT', details=details))
        if corrections and not self._stime:
            logging.warning('Shutdown time unknown for db integrity check.'
                            ' Used +1 second for ' + str(corrections) + ' correction events.')
        return None
