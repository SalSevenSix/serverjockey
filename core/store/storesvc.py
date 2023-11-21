import logging
import typing
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
# TODO ALLOW ???
from core.util import io, funcutil
from core.msg import msgabc, msgftr
from core.context import contextsvc
from core.store import storeabc, storesvctxn


class StoreService(msgabc.AbcSubscriber):
    INITIALISE = 'StoreService.Initialise'

    def __init__(self, context: contextsvc.Context):
        super().__init__(msgftr.Or(
            msgftr.NameIn((StoreService.INITIALISE, storeabc.TRANSACTION)),
            msgftr.IsStop()))
        self._context = context
        self._session: Session | None = None

    async def handle(self, message):
        if message is msgabc.STOP:
            await _close_session(self._session)
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
            self._session = await _create_session(database_path, create_database)
            if create_database:
                await _execute(self._session, storesvctxn.CreateDatabaseDone())
            else:
                await _execute(self._session, storesvctxn.IntegrityChecks(self._context))
        except Exception as e:
            logging.error('Error initialising database: ' + repr(e))
            await _close_session(self._session)
            self._session = None
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
            logging.error('Transaction error: ' + repr(e))
        finally:
            self._context.post(message.source(), storeabc.TRANSACTION_RESPONSE, result, message)


def _sync_create_session(database_path: str, create_database: bool) -> Session:
    engine = create_engine('sqlite:///' + database_path)
    if create_database:
        storeabc.Base.metadata.create_all(engine)
        logging.debug('Created database: ' + database_path)
    return Session(engine)


def _sync_execute(session: Session, transaction: storeabc.Transaction) -> typing.Any:
    with session.begin():
        return transaction.execute(session)


def _sync_close_session(session: Session):
    if not session:
        return
    try:
        session.close()
    except Exception as e:
        logging.debug('Error closing session: ' + repr(e))


_create_session = funcutil.to_async(_sync_create_session)
_execute = funcutil.to_async(_sync_execute)
_close_session = funcutil.to_async(_sync_close_session)
