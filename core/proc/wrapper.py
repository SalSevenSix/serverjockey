# ALLOW const.* util.* msg.* context.*
from core.util import io


async def write_wrapper(path: str) -> str:
    filename = path + '/wrapper.py'
    await io.write_file(filename, _wrapper_code())
    return filename


def _wrapper_code() -> str:
    # https://docs.python.org/3/library/pty.html
    return '''import sys
import os
import pty


def read(fd):
    return os.read(fd, 1024)


def main() -> int:
    try:
        return pty.spawn(sys.argv[1:], read)
    except Exception as e:
        print(repr(e), file=sys.stderr, flush=True)
    return 1


if __name__ == '__main__':
    sys.exit(main())
'''
