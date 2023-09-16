import logging
import os
import signal
# ALLOW util.*
from core.util import shellutil


def interrupt(pid: int):
    os.kill(pid, signal.SIGINT)  # This is probably blocking io but quick


def interrupt_self():
    interrupt(os.getpid())


async def kill_tree(pid: int):
    script = _kill_tree_script().strip().replace('{rootpid}', str(pid))
    await shellutil.run_script(script)


async def silently_kill_tree(pid: int):
    try:
        await kill_tree(pid)
    except Exception as e:
        logging.debug('silent_kill_tree() ' + repr(e))


def _kill_tree_script():
    return '''
gather_pids() {
  local children=$(ps -o pid= --ppid "$1")
  for pid in $children; do
    gather_pids "$pid"
  done
  echo "$children"
}
kill -9 $(gather_pids "{rootpid}") {rootpid}
'''
