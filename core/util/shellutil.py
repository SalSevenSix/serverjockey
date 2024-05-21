import logging
import asyncio
# ALLOW const.* util.util


async def run_script(script: str) -> str:
    _log('SCRIPT', script)
    process = await asyncio.create_subprocess_shell(
        script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return _handle_results(stdout, stderr)


async def run_executable(program: str, *arguments) -> str:
    _log('shl> PROGRAM', program + ' ' + repr(arguments))
    process = await asyncio.create_subprocess_exec(
        program, *arguments, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return _handle_results(stdout, stderr)


def _handle_results(stdout, stderr) -> str:
    result = None
    if stderr:
        _log('STDERR', stderr.decode())
    if stdout:
        result = stdout.decode().strip()
        _log('shl> STDOUT', result)
    return result


def _log(name: str, content: str):
    if not content:
        return
    content = content.strip()
    if content.find('\n') > -1:
        name += '\n'
    else:
        name += ' '
    logging.debug(name + content)
