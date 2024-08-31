import subprocess
import pkgutil
import time
# ALLOW NONE

OUT = '    '
GET, POST = 'GET', 'POST'
DEFAULT_SERVICE = 'serverjockey'
DEFAULT_USER = 'sjgms'
DEFAULT_PORT = 6164


def get_resource(name: str) -> str | None:
    result = pkgutil.get_data('rsc', name)
    return result.decode() if result else None


def split_argument(argument: str | None, expected: int) -> tuple:
    assert expected > 0
    result = []
    index = expected
    while index > 0:
        result.append(None)
        index -= 1
    if argument is not None:
        for part in argument.split(','):
            if index < expected:
                result[index] = part
                index += 1
    return tuple(result)


def repr_dict(obj: dict, prefix: str = '') -> str:
    result = ''
    if prefix:
        prefix += '-'
    for key, value in obj.items():
        if isinstance(value, dict):
            result += repr_dict(value, prefix + str(key))
        else:
            result += prefix + str(key) + ': ' + str(value) + '\n'
    return result


def to_int(value: str | None, fallback: int = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def get_local_ip4() -> str:
    # noinspection PyBroadException
    try:
        return get_local_ips()[0][0]  # first ipv4
    except Exception:
        return 'localhost'


def get_local_ips() -> tuple:
    result, count = _get_local_ips(), 6
    while len(result[0]) == 0 and len(result[1]) == 0 and count > 0:
        time.sleep(4.0)
        result = _get_local_ips()
        count -= 1
    return result


def _get_local_ips() -> tuple:
    result = subprocess.run(('hostname', '-I'), capture_output=True)
    result = result.stdout if result.returncode == 0 else None
    return _extract_hostname_ips(result)


def _extract_hostname_ips(hostnames: str | bytes | None) -> tuple:
    data = hostnames.decode() if isinstance(hostnames, bytes) else hostnames
    data, ipv4, ipv6 = data.strip() if data else None, [], []
    if not data:
        return tuple(ipv4), tuple(ipv6)
    for item in data.split():
        len_item = len(item)
        if len(item.replace('.', '')) == (len_item - 3):
            ipv4.append(item)
        elif len(item.replace(':', '')) == (len_item - 7):
            ipv6.append(item)
    return tuple(ipv4), tuple(ipv6)
