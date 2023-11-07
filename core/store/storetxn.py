import typing
import time
from sqlalchemy import Executable
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
# TODO ALLOW ???
from core.util import util
from core.store import storeabc

_CACHE_INSTANCE_ID = {}
_CACHE_PLAYER_ID = {}


async def _load_instance(session: AsyncSession, identity: str) -> storeabc.Instance | None:
    results = await session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == identity))
    return results.first()


async def _get_instance_id(session: AsyncSession, identity: str) -> int:
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


class SelectInstanceEvent(storeabc.Transaction):

    def __init__(self, identity: str | None):
        self._identity = identity

    async def execute(self, session: AsyncSession) -> typing.Any:
        statement = select(storeabc.InstanceEvent.at, storeabc.Instance.name, storeabc.InstanceEvent.name)
        statement = statement.join(storeabc.Instance.events)
        if self._identity:
            instance_id = await _get_instance_id(session, self._identity)
            statement = statement.where(storeabc.Instance.id == instance_id)
        return await _execute_query(session, statement, 'at', 'instance', 'event')


async def _execute_query(session: AsyncSession, statement: Executable, *columns: str) -> tuple:
    results = []
    for row in await session.execute(statement):
        result, index = {}, 0
        for column in columns:
            value = row[index]
            result[column] = value
            index += 1
        results.append(result)
    return tuple(results)
