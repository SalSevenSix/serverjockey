import json
import typing
# ALLOWutil.*


def to_bool(value: typing.Any) -> bool:
    if not value:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'y', 'yes', 'on')
    if isinstance(value, (int, float)):
        return value > 0.0
    return True


def obj_to_str(obj: typing.Any) -> str:
    value = repr(obj)
    if obj is None or isinstance(obj, (str, tuple, list, dict, bool, int, float)):
        return value
    result = value.replace(' object at ', ':')
    if result == value:
        return result
    return result[:-1].split('.')[-1]


def obj_to_dict(obj: typing.Any) -> typing.Optional[dict]:
    if obj is None or isinstance(obj, dict):
        return obj
    if hasattr(obj, 'asdict'):
        return obj.asdict()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise Exception('obj_to_dict() failed converting {} to dict'.format(obj))


def obj_to_json(obj: typing.Any, pretty: bool = False) -> typing.Optional[str]:
    if obj is None:
        return None
    encoder = None if isinstance(obj, dict) else _JsonEncoder
    if hasattr(obj, '__dict__'):
        obj = obj.__dict__
    # noinspection PyBroadException
    try:
        if pretty:
            return json.dumps(obj, cls=encoder, indent=2, separators=(',', ': '))
        return json.dumps(obj, cls=encoder)
    except Exception:
        return None


def json_to_dict(text: str) -> typing.Optional[dict]:
    # noinspection PyBroadException
    try:
        return json.loads(text)
    except Exception:
        return None


class _JsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if obj is None or type(obj) in (str, tuple, list, dict):
            return obj
        return obj_to_str(obj)
