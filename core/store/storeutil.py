import re
from sqlalchemy import Executable
from sqlalchemy.orm import Session
from sqlalchemy.future import select
# ALLOW util.* store.storeabc
from core.util import util, dtutil
from core.store import storeabc

# Note that all this is blocking IO

_CACHE_INSTANCE_ID, _CACHE_PLAYER_ID = {}, {}
_NOT_FLAG_REGEX = re.compile(r'[^gmixsuUAJD]')


def to_regex(value: str) -> tuple:
    if not value:
        return None, None
    value = value.strip()
    if len(value) < 3 or value[0] != '/':
        return None, None
    index = value.rfind('/')
    if index <= 0 or value[index - 1] == '\\':
        return None, None
    flags = value[index + 1:]
    if flags and _NOT_FLAG_REGEX.search(flags):
        return None, None
    value = value[1:index]
    try:
        re.compile(value)
    except re.error:
        return None, None
    return value, flags if flags else None


def clear_cache():
    _CACHE_PLAYER_ID.clear()
    _CACHE_INSTANCE_ID.clear()


def clear_cache_for(instance: storeabc.Instance):
    if util.get(instance.id, _CACHE_PLAYER_ID):
        del _CACHE_PLAYER_ID[instance.id]
    if util.get(instance.name, _CACHE_INSTANCE_ID):
        del _CACHE_INSTANCE_ID[instance.name]


def load_instance(session: Session, identity: str) -> storeabc.Instance | None:
    assert identity and identity == util.script_escape(identity)
    # noinspection PyTypeChecker
    results = session.scalars(select(storeabc.Instance).where(storeabc.Instance.name == identity))
    return results.first()


def get_instance_id(session: Session, identity: str) -> int:
    assert identity and identity == util.script_escape(identity)
    instance_id = util.get(identity, _CACHE_INSTANCE_ID)
    if instance_id:
        return instance_id
    instance = load_instance(session, identity)
    assert instance is not None
    instance_id = instance.id
    _CACHE_INSTANCE_ID[identity] = instance_id
    return instance_id


def lookup_player_id(session: Session, instance_id: int, player_name: str) -> int | None:
    player_cache = util.get(instance_id, _CACHE_PLAYER_ID)
    if not player_cache:
        player_cache = {}
        _CACHE_PLAYER_ID[instance_id] = player_cache
    player_id = util.get(player_name, player_cache)
    if player_id:
        return player_id
    # noinspection PyTypeChecker
    results = session.scalars(select(storeabc.Player).where(
        storeabc.Player.instance_id == instance_id,
        storeabc.Player.name == player_name))
    player = results.first()
    if not player:
        return None
    player_id = player.id
    player_cache[player_name] = player_id
    return player_id


def execute_query(session: Session, statement: Executable, criteria: dict, *columns: str) -> dict:
    result, records = dict(created=dtutil.now_millis(), criteria=criteria, headers=columns), []
    for row in session.execute(statement):
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
