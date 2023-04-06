import subprocess


def to_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    return None


def get_ip() -> str:
    result = subprocess.run(('hostname', '-I'), capture_output=True)
    if result.returncode != 0 or not result.stdout:
        return 'localhost'
    result = result.stdout.decode().strip().split()
    return result[0]
