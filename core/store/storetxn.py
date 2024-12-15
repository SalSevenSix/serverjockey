import typing
import time
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.future import select
# ALLOW util.* store.storeabc, store.storeutil
from core.util import util, dtutil
from core.store import storeabc, storeutil

# Note that all this is blocking IO


class InsertInstance(storeabc.Transaction):

    def __init__(self, identity: str, module: str):
        self._identity, self._module = identity, module

    def execute(self, session: Session) -> typing.Any:
        instance = storeutil.load_instance(session, self._identity)
        if not instance:
            session.add(storeabc.Instance(at=time.time(), name=self._identity, module=self._module))
        return None


class DeleteInstance(storeabc.Transaction):

    def __init__(self, identity: str):
        self._identity = identity

    def execute(self, session: Session) -> typing.Any:
        instance = storeutil.load_instance(session, self._identity)
        if instance:
            storeutil.clear_cache_for(instance)
            session.delete(instance)
        return None


class InsertInstanceEvent(storeabc.Transaction):

    def __init__(self, identity: str, name: str, details: str):
        self._identity = identity
        self._name, self._details = name, details

    def execute(self, session: Session) -> typing.Any:
        instance_id = storeutil.get_instance_id(session, self._identity)
        session.add(storeabc.InstanceEvent(at=time.time(), instance_id=instance_id,
                                           name=self._name, details=self._details))
        return None


class InsertPlayerEvent(storeabc.Transaction):

    def __init__(self, identity: str, event_name: str, player_name: str, steamid: str | None):
        self._identity = identity
        self._event_name, self._player_name, self._steamid = event_name, player_name, steamid

    def execute(self, session: Session) -> typing.Any:
        instance_id = storeutil.get_instance_id(session, self._identity)
        player_id = storeutil.lookup_player_id(session, instance_id, self._player_name)
        now = time.time()
        if not player_id:
            player = storeabc.Player(at=now, instance_id=instance_id, name=self._player_name, steamid=self._steamid)
            session.add(player)
            session.flush()
            player_id = player.id
        session.add(storeabc.PlayerEvent(at=now, player_id=player_id, name=self._event_name, details=None))
        return None


class InsertPlayerChat(storeabc.Transaction):

    def __init__(self, identity: str, player_name: str, text: str):
        self._identity = identity
        self._player_name, self._text = player_name, text

    def execute(self, session: Session) -> typing.Any:
        instance_id = storeutil.get_instance_id(session, self._identity)
        player_id = storeutil.lookup_player_id(session, instance_id, self._player_name)
        if player_id:
            session.add(storeabc.PlayerChat(at=time.time(), player_id=player_id, text=self._text))
        return None


class SelectInstance(storeabc.Transaction):

    def __init__(self, data: dict):
        self._data = data

    def execute(self, session: Session) -> typing.Any:
        criteria = util.filter_dict(self._data, ('instance', ), True)
        instance = util.get('instance', criteria)
        statement = select(storeabc.Instance.at, storeabc.Instance.name, storeabc.Instance.module)
        if instance:
            # noinspection PyTypeChecker
            statement = statement.where(storeabc.Instance.id == storeutil.get_instance_id(session, instance))
        return storeutil.execute_query(session, statement, criteria, 'at', 'name', 'module')


class SelectInstanceEvent(storeabc.Transaction):

    def __init__(self, data: dict):
        self._data = data

    def execute(self, session: Session) -> typing.Any:
        criteria = util.filter_dict(self._data, ('instance', 'events', 'atfrom', 'atto', 'atgroup'), True)
        instance, events, at_from, at_to, at_group = util.unpack_dict(criteria)
        statement = select(storeabc.InstanceEvent.at, storeabc.Instance.name, storeabc.InstanceEvent.name)
        statement = statement.join(storeabc.Instance.events)
        if instance:
            # noinspection PyTypeChecker
            statement = statement.where(storeabc.Instance.id == storeutil.get_instance_id(session, instance))
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
        if events:
            statement = statement.where(storeabc.InstanceEvent.name.in_(str(events).upper().split(',')))
        if at_group:
            if at_group not in ('min', 'max'):
                raise Exception('Invalid atgroup')
            statement = statement.group_by(storeabc.InstanceEvent.instance_id)
            statement = statement.having(
                func.max(storeabc.InstanceEvent.at) if at_group == 'max' else func.min(storeabc.InstanceEvent.at))
        statement = statement.order_by(storeabc.InstanceEvent.at)
        criteria['atfrom'], criteria['atto'] = at_from, at_to
        return storeutil.execute_query(session, statement, criteria, 'at', 'instance', 'event')


class SelectPlayerEvent(storeabc.Transaction):

    def __init__(self, data: dict):
        self._data = data

    def execute(self, session: Session) -> typing.Any:
        criteria = util.filter_dict(self._data, ('instance', 'atfrom', 'atto', 'atgroup', 'player', 'verbose'), True)
        instance, at_from, at_to, at_group, player, verbose = util.unpack_dict(criteria)
        columns = ['at', 'instance', 'player', 'event']
        entities = [storeabc.PlayerEvent.at, storeabc.Instance.name, storeabc.Player.name, storeabc.PlayerEvent.name]
        if verbose is not None:
            columns.append('steamid')
            entities.append(storeabc.Player.steamid)
        statement = select(*entities).join(storeabc.Instance.players).join(storeabc.Player.events)
        if instance:
            # noinspection PyTypeChecker
            statement = statement.where(storeabc.Instance.id == storeutil.get_instance_id(session, instance))
        if at_from:
            at_from = int(at_from)
            if at_group:
                statement = statement.where(storeabc.PlayerEvent.at > dtutil.to_seconds(at_from))
            else:
                statement = statement.where(storeabc.PlayerEvent.at >= dtutil.to_seconds(at_from))
        if at_to:
            at_to = int(at_to)
            if at_group:
                statement = statement.where(storeabc.PlayerEvent.at < dtutil.to_seconds(at_to))
            else:
                statement = statement.where(storeabc.PlayerEvent.at <= dtutil.to_seconds(at_to))
        if player:
            regex, flags = storeutil.to_regex(player)
            if regex:
                statement = statement.where(storeabc.Player.name.regexp_match(regex, flags))
            else:
                # noinspection PyTypeChecker
                statement = statement.where(storeabc.Player.name == util.script_escape(player))
        if at_group:
            if at_group not in ('min', 'max'):
                raise Exception('Invalid atgroup')
            statement = statement.group_by(storeabc.PlayerEvent.player_id)
            statement = statement.having(
                func.max(storeabc.PlayerEvent.at) if at_group == 'max' else func.min(storeabc.PlayerEvent.at))
        statement = statement.order_by(storeabc.PlayerEvent.at)
        criteria['atfrom'], criteria['atto'] = at_from, at_to
        return storeutil.execute_query(session, statement, criteria, *columns)


class SelectPlayerChat(storeabc.Transaction):

    def __init__(self, data: dict):
        self._data = data

    def execute(self, session: Session) -> typing.Any:
        criteria = util.filter_dict(self._data, ('instance', 'atfrom', 'atto', 'player'), True)
        instance, at_from, at_to, player = util.unpack_dict(criteria)
        statement = select(storeabc.PlayerChat.at, storeabc.Player.name, storeabc.PlayerChat.text)
        statement = statement.join(storeabc.Player.chats)
        statement = statement.where(storeabc.Player.instance_id == storeutil.get_instance_id(session, instance))
        if at_from:
            at_from = int(at_from)
            statement = statement.where(storeabc.PlayerChat.at >= dtutil.to_seconds(at_from))
        if at_to:
            at_to = int(at_to)
            statement = statement.where(storeabc.PlayerChat.at <= dtutil.to_seconds(at_to))
        if player:
            regex, flags = storeutil.to_regex(player)
            if regex:
                statement = statement.where(storeabc.Player.name.regexp_match(regex, flags))
            else:
                # noinspection PyTypeChecker
                statement = statement.where(storeabc.Player.name == util.script_escape(player))
        statement = statement.order_by(storeabc.PlayerChat.at)
        criteria['atfrom'], criteria['atto'] = at_from, at_to
        return storeutil.execute_query(session, statement, criteria, 'at', 'player', 'text')
