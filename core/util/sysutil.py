import logging
import shutil
import asyncio
import aiohttp
# ALLOW util.*
from core.util import __version__, funcutil, shellutil


_disk_usage = funcutil.to_async(shutil.disk_usage)
# _virtual_memory = funcutil.to_async(psutil.virtual_memory)
# _cpu_percent = funcutil.to_async(psutil.cpu_percent)


async def get_local_ip() -> str:
    if NET.local_ip:
        return NET.local_ip
    # noinspection PyBroadException
    try:
        result = await shellutil.run_script('hostname -I')
        NET.local_ip = result.strip().split()[0]
        return NET.local_ip
    except Exception as e:
        logging.error('get_local_ip() failed %s', repr(e))
    return 'localhost'


async def get_public_ip() -> str:
    if NET.public_ip:
        return NET.public_ip
    for url in ('https://api.ipify.org', 'https://ip4.seeip.org'):
        NET.public_ip = await _fetch_text(url)
        if NET.public_ip:
            return NET.public_ip
    NET.public_ip = 'UNAVAILABLE'
    return NET.public_ip


async def _fetch_text(url: str) -> str | None:
    # noinspection PyBroadException
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                assert response.status == 200
                result = await response.text()
                return result.strip()
    except Exception as e:
        logging.error('Failed to get public ip from %s because %s', url, repr(e))
    return None


async def _virtual_memory() -> tuple:
    result = await shellutil.run_script('free -b | grep "Mem:"')
    if not result:
        return -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
    result = result.strip().split(' ')
    result.pop(0)
    result = [i for i in result if i != '']
    result = [int(i) for i in result]
    result = [result[0], result[5], round(float(result[1] / result[0] * 100), 1),
              result[1], result[2], -1, -1, -1, result[4], -1, -1]
    return tuple(result)


async def _cpu_percent() -> float:
    result = await shellutil.run_script('top -b -n 2 | grep "%Cpu(s)" | tail -1')
    result = result.strip().split(' ')
    result = [i for i in result if i != '']
    result = result[result.index('id,') - 1]
    if result == 'ni,100.0':
        return 0.0
    return round(100.0 - float(result), 1)


def system_version() -> str:
    return __version__


async def system_info() -> dict:
    cpu, memory, disk, local_ip, public_ip = await asyncio.gather(
        _cpu_percent(), _virtual_memory(), _disk_usage('/'), get_local_ip(), get_public_ip())
    return {
        'version': system_version(),
        'cpu': {
            'percent': cpu
        },
        'memory': {
            'total': memory[0],
            'used': memory[3],
            'available': memory[1],
            'free': memory[4],
            'percent': memory[2]
        },
        'disk': {
            'total': disk[0],
            'used': disk[1],
            'free': disk[2],
            'percent': round((disk[1] / disk[0]) * 100, 1)
        },
        'net': {
            'local': local_ip,
            'public': public_ip
        }
    }


# TODO utils probably should not cache or hold statefulness
class NetCache:
    def __init__(self):
        self.local_ip, self.public_ip = '', ''


NET = NetCache()
