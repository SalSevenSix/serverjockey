import logging
import asyncio
# ALLOW util.util


async def run_script(script: str) -> str:
    logging.debug('SCRIPT\n' + script)
    process = await asyncio.create_subprocess_shell(
        script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if stderr:
        logging.error('STDERR\n' + stderr.decode())
    result = None
    if stdout:
        result = stdout.decode()
        logging.debug('STDOUT\n' + result)
    return result
