import sys

# https://docs.python.org/3/library/pty.html


def main() -> int:
    running = True
    while running:
        line = sys.stdin.readline()
        line = line.strip()
        if line == 'quit':
            print('QUIT', flush=True)
            running = False
        else:
            print('OK> ' + line, flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
