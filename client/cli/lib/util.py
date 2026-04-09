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


def rchop(value: str, keyword: str, strip: bool = True) -> str:
    index = value.find(keyword)
    if index == -1:
        return value
    value = value[:index]
    return value.strip() if strip else value


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
    result = subprocess.run(('ip', 'route'), capture_output=True)
    if result.returncode == 0:
        result = _extract_iproute_adaptor(result.stdout)
        if result:
            result = subprocess.run(('ip', '-br', 'address', 'show', result), capture_output=True)
            if result.returncode == 0:
                return _extract_ipaddrshow_ips(result.stdout)
    return (), ()


def _extract_iproute_adaptor(value: str | bytes | None) -> str | None:
    data = value.decode() if isinstance(value, bytes) else value
    data = data.strip().split('\n') if data else []
    found = False
    for line in data:
        if line.find('default') > -1:
            for item in line.strip().split():
                if found:
                    return item
                found = item == 'dev'
    return None


def _extract_ipaddrshow_ips(value: str | bytes | None) -> tuple:
    data = value.decode() if isinstance(value, bytes) else value
    data = data.strip().split() if data else []
    ipv4, ipv6 = [], []
    for item in data:
        if item:
            ipval = rchop(item, '/')
            if ipval.count('.') == 3:
                ipv4.append(ipval)
            elif ipval.count(':') > 1:
                ipv6.append(ipval)
    return tuple(ipv4), tuple(ipv6)
