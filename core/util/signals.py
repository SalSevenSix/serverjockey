import typing
import logging
import os
import signal
# ALLOW util.*
from core.util import shellutil


def interrupt(pid: typing.Optional[int] = None):
    if pid is None:
        pid = os.getpid()
    os.kill(pid, signal.SIGINT)


async def kill_tree(pid: int):
    pid_str = str(pid)
    script = '\n'.join(
        ['ps --ppid ' + pid_str + ' -o pid= | awk {\'print$1\'} | while read pid; do',
         '  kill -9 $pid', 'done',
         'kill -9 ' + pid_str])
    await shellutil.run_script(script)


async def silently_kill_tree(pid: int):
    try:
        await kill_tree(pid)
    except Exception as e:
        logging.debug('silent_kill_tree() ' + repr(e))
