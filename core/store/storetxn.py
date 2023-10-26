import typing
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
# TODO ALLOW ???
from core.store import storeabc


class InsertInstance(storeabc.Transaction):

    def __init__(self, subcontext):
        self._identity, self._module = str(subcontext.config('identity')), subcontext.config('module')

    async def execute(self, session: AsyncSession) -> typing.Any:
        results = await session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == self._identity))
        if not results.first():
            session.add(storeabc.Instance(created_at=datetime.now(), name=self._identity, module=self._module))
        return None


class DeleteInstance(storeabc.Transaction):

    def __init__(self, subcontext):
        self._identity = str(subcontext.config('identity'))

    async def execute(self, session: AsyncSession) -> typing.Any:
        results = await session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == self._identity))
        instance = results.first()
        if instance:
            await session.delete(instance)
        return None


class InsertInstanceEvent(storeabc.Transaction):

    def __init__(self, subcontext, name: str, details: str):
        self._identity = str(subcontext.config('identity'))
        self._name, self._details = name, details

    async def execute(self, session: AsyncSession) -> typing.Any:
        results = await session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == self._identity))
        session.add(storeabc.InstanceEvent(at=datetime.now(), instance=results.one().id,
                                           name=self._name, details=self._details))
        return None


class InsertPlayerEvent(storeabc.Transaction):

    def __init__(self, subcontext, event_name: str, player_name: str, steamid: str | None):
        self._identity = str(subcontext.config('identity'))
        self._event_name, self._player_name, self._steamid = event_name, player_name, steamid

    async def execute(self, session: AsyncSession) -> typing.Any:
        results = await session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == self._identity))
        instance_id = results.one().id
        results = await session.scalars(select(storeabc.Player).where(
            storeabc.Player.instance == instance_id,
            storeabc.Player.name == self._player_name))
        player = results.first()
        if not player:
            player = storeabc.Player(instance=instance_id, name=self._player_name, steamid=self._steamid)
            session.add(player)
            await session.flush()
        session.add(storeabc.PlayerEvent(at=datetime.now(), player=player.id, name=self._event_name))
        return None


class InsertPlayerChat(storeabc.Transaction):

    def __init__(self, subcontext, player_name: str, text: str):
        self._identity = str(subcontext.config('identity'))
        self._player_name, self._text = player_name, text

    async def execute(self, session: AsyncSession) -> typing.Any:
        results = await session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == self._identity))
        results = await session.scalars(select(storeabc.Player).where(
            storeabc.Player.instance == results.one().id,
            storeabc.Player.name == self._player_name))
        player = results.first()
        if player:
            session.add(storeabc.PlayerChat(at=datetime.now(), player=player.id, text=self._text))
        return None
