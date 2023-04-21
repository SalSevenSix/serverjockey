import sys
import os
import pty  # https://docs.python.org/3/library/pty.html
# ALLOW NONE


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
