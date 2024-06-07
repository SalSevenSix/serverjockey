import logging
import os
import signal
# ALLOW util.*
from core.util import shellutil


def pid_self():
    return os.getpid()


def interrupt(pid: int):
    os.kill(pid, signal.SIGINT)  # This is probably blocking io but quick


def interrupt_self():
    interrupt(pid_self())


async def kill_tree(pid: int):
    script = _kill_tree_script().strip().replace('{rootpid}', str(pid))
    await shellutil.run_script(script)


async def silently_kill_tree(pid: int):
    try:
        await kill_tree(pid)
    except Exception as e:
        logging.debug('silent_kill_tree() ' + repr(e))


async def get_leaf(pid: int) -> int | None:
    if not pid:
        return None
    script = _leaf_pid_script().strip().replace('{rootpid}', str(pid))
    try:
        return int(await shellutil.run_script(script))
    except Exception as e:
        logging.debug('get_leaf_pid() ' + repr(e))
    return None


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


def _leaf_pid_script():
    return '''
pid_chain() {
  local child=$(ps -o pid= --ppid "$1" | head -1 | tr -d '[:space:]')
  [ -z "$child" ] || pid_chain "$child"
  echo "$1"
}
pid_chain "{rootpid}" | head -1
'''
