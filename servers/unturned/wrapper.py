import sys
import os
import pty  # https://docs.python.org/3/library/pty.html


def read(fd):
    return os.read(fd, 1024)


def main() -> int:
    status = 1
    try:
        pty.spawn(sys.argv[1], read)
        status = 0
    except Exception as e:
        print(repr(e), file=sys.stderr, flush=True)
    return status


if __name__ == '__main__':
    sys.exit(main())
