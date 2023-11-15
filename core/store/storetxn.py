import typing
import time
from sqlalchemy import Executable, func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
# TODO ALLOW ???
from core.util import util, dtutil
from core.store import storeabc

_CACHE_INSTANCE_ID = {}
_CACHE_PLAYER_ID = {}


async def _load_instance(session: AsyncSession, identity: str) -> storeabc.Instance | None:
    assert identity == util.script_escape(identity)
    results = await session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == identity))
    return results.first()


async def _get_instance_id(session: AsyncSession, identity: str) -> int:
    assert identity == util.script_escape(identity)
    instance_id = util.get(identity, _CACHE_INSTANCE_ID)
    if instance_id:
        return instance_id
    instance = await _load_instance(session, identity)
    assert instance is not None
    instance_id = instance.id
    _CACHE_INSTANCE_ID[identity] = instance_id
    return instance_id


async def _lookup_player_id(session: AsyncSession, instance_id: int, player_name: str) -> int | None:
    player_cache = util.get(instance_id, _CACHE_PLAYER_ID)
    if not player_cache:
        player_cache = {}
        _CACHE_PLAYER_ID[instance_id] = player_cache
    player_id = util.get(player_name, player_cache)
    if player_id:
        return player_id
    results = await session.scalars(select(storeabc.Player).where(
        storeabc.Player.instance_id == instance_id,
        storeabc.Player.name == player_name))
    player = results.first()
    if not player:
        return None
    player_id = player.id
    player_cache[player_name] = player_id
    return player_id


class InsertInstance(storeabc.Transaction):

    def __init__(self, identity: str, module: str):
        self._identity, self._module = identity, module

    async def execute(self, session: AsyncSession) -> typing.Any:
        instance = await _load_instance(session, self._identity)
        if not instance:
            session.add(storeabc.Instance(at=time.time(), name=self._identity, module=self._module))
        return None


class DeleteInstance(storeabc.Transaction):

    def __init__(self, identity: str):
        self._identity = identity

    async def execute(self, session: AsyncSession) -> typing.Any:
        instance = await _load_instance(session, self._identity)
        if not instance:
            return None
        if util.get(instance.id, _CACHE_PLAYER_ID):
            del _CACHE_PLAYER_ID[instance.id]
        if util.get(instance.name, _CACHE_INSTANCE_ID):
            del _CACHE_INSTANCE_ID[instance.name]
        await session.delete(instance)
        return None


class InsertInstanceEvent(storeabc.Transaction):

    def __init__(self, identity: str, name: str, details: str):
        self._identity = identity
        self._name, self._details = name, details

    async def execute(self, session: AsyncSession) -> typing.Any:
        instance_id = await _get_instance_id(session, self._identity)
        session.add(storeabc.InstanceEvent(at=time.time(), instance_id=instance_id,
                                           name=self._name, details=self._details))
        return None


class InsertPlayerEvent(storeabc.Transaction):

    def __init__(self, identity: str, event_name: str, player_name: str, steamid: str | None):
        self._identity = identity
        self._event_name, self._player_name, self._steamid = event_name, player_name, steamid

    async def execute(self, session: AsyncSession) -> typing.Any:
        instance_id = await _get_instance_id(session, self._identity)
        player_id = await _lookup_player_id(session, instance_id, self._player_name)
        now = time.time()
        if not player_id:
            player = storeabc.Player(at=now, instance_id=instance_id, name=self._player_name, steamid=self._steamid)
            session.add(player)
            await session.flush()
            player_id = player.id
        session.add(storeabc.PlayerEvent(at=now, player_id=player_id, name=self._event_name, details=None))
        return None


class InsertPlayerChat(storeabc.Transaction):

    def __init__(self, identity: str, player_name: str, text: str):
        self._identity = identity
        self._player_name, self._text = player_name, text

    async def execute(self, session: AsyncSession) -> typing.Any:
        instance_id = await _get_instance_id(session, self._identity)
        player_id = await _lookup_player_id(session, instance_id, self._player_name)
        if player_id:
            session.add(storeabc.PlayerChat(at=time.time(), player_id=player_id, text=self._text))
        return None


class SelectInstance(storeabc.Transaction):

    def __init__(self, data: dict):
        self._data = data

    async def execute(self, session: AsyncSession) -> typing.Any:
        criteria = util.filter_dict(self._data, ('instance', ), True)
        instance = util.get('instance', criteria)
        statement = select(storeabc.Instance.at, storeabc.Instance.name, storeabc.Instance.module)
        if instance:
            statement = statement.where(storeabc.Instance.id == await _get_instance_id(session, instance))
        return await _execute_query(session, statement, criteria, 'at', 'name', 'module')


class SelectInstanceEvent(storeabc.Transaction):

    def __init__(self, data: dict):
        self._data = data

    async def execute(self, session: AsyncSession) -> typing.Any:
        criteria = util.filter_dict(self._data, ('instance', 'events', 'atfrom', 'atto', 'atgroup'), True)
        instance, events, at_from, at_to, at_group = util.unpack_dict(criteria)
        statement = select(storeabc.InstanceEvent.at, storeabc.Instance.name, storeabc.InstanceEvent.name)
        statement = statement.join(storeabc.Instance.events)
        if instance:
            statement = statement.where(storeabc.Instance.id == await _get_instance_id(session, instance))
        if events:
            statement = statement.where(storeabc.InstanceEvent.name.in_(str(events).upper().split(',')))
        if at_from:
            at_from = int(at_from)
            if at_group:
                statement = statement.where(storeabc.InstanceEvent.at > dtutil.to_seconds(at_from))
            else:
                statement = statement.where(storeabc.InstanceEvent.at >= dtutil.to_seconds(at_from))
        if at_to:
            at_to = int(at_to)
            if at_group:
                statement = statement.where(storeabc.InstanceEvent.at < dtutil.to_seconds(at_to))
            else:
                statement = statement.where(storeabc.InstanceEvent.at <= dtutil.to_seconds(at_to))
        if at_group:
            if at_group not in ('min', 'max'):
                raise Exception('Invalid atgroup')
            statement = statement.group_by(storeabc.InstanceEvent.instance_id)
            statement = statement.having(
                func.max(storeabc.InstanceEvent.at) if at_group == 'max' else func.min(storeabc.InstanceEvent.at))
        statement = statement.order_by(storeabc.InstanceEvent.at)
        criteria['atfrom'], criteria['atto'] = at_from, at_to
        return await _execute_query(session, statement, criteria, 'at', 'instance', 'event')


async def _execute_query(session: AsyncSession, statement: Executable, criteria: dict, *columns: str) -> dict:
    result, records = {'created': dtutil.now_millis(), 'criteria': criteria, 'headers': columns}, []
    for row in await session.execute(statement):
        record, index = [], 0
        for column in columns:
            value = row[index]
            if column == 'at':
                value = dtutil.to_millis(value)
            record.append(value)
            index += 1
        records.append(record)
    result['records'] = records
    return result
