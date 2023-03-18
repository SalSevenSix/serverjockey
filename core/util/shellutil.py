import logging
import asyncio


async def run_script(script: str) -> str:
    logging.debug('SCRIPT\n' + script)
    process = await asyncio.create_subprocess_shell(
        script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    result = None
    stdout, stderr = await process.communicate()
    if stderr:
        logging.error('STDERR\n' + stderr.decode())
    if stdout:
        result = stdout.decode()
        logging.debug('STDOUT\n' + result)
    return result
