import typing
import os
import signal


def interrupt(pid: typing.Optional[int] = None):
    if pid is None:
        pid = os.getpid()
    os.kill(pid, signal.SIGINT)
