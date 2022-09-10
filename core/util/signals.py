import logging
import typing
import os
import asyncio
import signal


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
    await _run_script(script)


async def _run_script(script: str):
    logging.debug('SCRIPT\n' + script)
    process = await asyncio.create_subprocess_shell(
        script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if stdout:
        logging.debug('STDOUT\n' + stdout.decode())
    if stderr:
        logging.error('STDERR\n' + stderr.decode())
