import subprocess
# ALLOW NONE


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


def get_ip() -> str:
    result = subprocess.run(('hostname', '-I'), capture_output=True)
    if result.returncode != 0 or not result.stdout:
        return 'localhost'
    result = result.stdout.decode().strip().split()
    return result[0]
