import logging
import typing
import time
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.future import select
# ALLOW util.* msg*.* context.* store.storeabc
from core.util import sysutil, objconv
from core.msgc import sc
from core.context import contextsvc
from core.store import storeabc

# Note that all this is blocking IO


class StoreCreatedEvent(storeabc.Transaction):

    def execute(self, session: Session) -> typing.Any:
        session.add(storeabc.SystemEvent(
            at=time.time(), name='SCHEMA',
            details=objconv.obj_to_json(sysutil.system_version_dict())))
        return None


class StoreResetEvent(storeabc.Transaction):

    def execute(self, session: Session) -> typing.Any:
        session.add(storeabc.SystemEvent(at=time.time(), name='RESET', details=None))
        return None


class IntegrityChecks(storeabc.Transaction):

    def __init__(self, context: contextsvc.Context):
        self._context = context

    def execute(self, session: Session) -> typing.Any:
        stime, corrections = self._context.config('stime'), 0
        emap = {sc.START: sc.EXCEPTION, sc.STARTING: sc.EXCEPTION, sc.STARTED: sc.EXCEPTION,
                sc.STOPPING: sc.STOPPED, sc.MAINTENANCE: sc.READY}
        details = objconv.obj_to_json({'error': 'Event inserted by startup integrity check'})
        statement = select(storeabc.InstanceEvent)
        statement = statement.group_by(storeabc.InstanceEvent.instance_id)
        statement = statement.having(storeabc.InstanceEvent.name.in_(emap.keys()))
        statement = statement.having(func.max(storeabc.InstanceEvent.at))
        for event in session.scalars(statement):
            corrections += 1
            event_at = stime if stime and stime > event.at else event.at + 1.0
            session.add(storeabc.InstanceEvent(
                at=event_at, instance_id=event.instance_id, name=emap[event.name], details=details))
            logging.debug('InstanceEvent correction: ' + str(event.instance_id) + ' ' + emap[event.name])
        statement = select(storeabc.PlayerEvent)
        statement = statement.group_by(storeabc.PlayerEvent.player_id)
        statement = statement.having(storeabc.PlayerEvent.name == 'LOGIN')
        statement = statement.having(func.max(storeabc.PlayerEvent.at))
        for event in session.scalars(statement):
            corrections += 1
            event_at = stime if stime and stime > event.at else event.at + 1.0
            session.add(storeabc.PlayerEvent(
                at=event_at, player_id=event.player_id, name='LOGOUT', details=details))
            logging.debug('PlayerEvent correction: ' + str(event.player_id) + ' LOGOUT')
        if corrections and not stime:
            logging.warning('Shutdown time unknown for db integrity check.'
                            ' Used +1 second for ' + str(corrections) + ' correction events.')
        return None
