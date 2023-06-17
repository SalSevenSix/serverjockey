import logging
import shutil
import asyncio
import aiohttp
import socket
# ALLOW util.*
from core.util import util, io, funcutil, shellutil

_CACHE = {}  # TODO utils probably should not cache or hold statefulness

_disk_usage = funcutil.to_async(shutil.disk_usage)
# _virtual_memory = funcutil.to_async(psutil.virtual_memory)
# _cpu_percent = funcutil.to_async(psutil.cpu_percent)


async def get_os_name() -> str:
    result = util.get('os_name', _CACHE)
    if result:
        return result
    file = '/etc/os-release'
    # noinspection PyBroadException
    try:
        if await io.file_exists(file):
            data = await io.read_file(file)
            for line in data.split('\n'):
                if line.startswith('PRETTY_NAME="'):
                    _CACHE['os_name'] = line[13:-1]
                    return _CACHE['os_name']
    except Exception as e:
        logging.error('get_os_name() failed %s', repr(e))
    _CACHE['os_name'] = 'UNKNOWN'
    return _CACHE['os_name']


async def get_local_ip() -> str:
    result = util.get('local_ip', _CACHE)
    if result:
        return result
    # noinspection PyBroadException
    try:
        result = await shellutil.run_script('hostname -I')
        _CACHE['local_ip'] = result.strip().split()[0]
        return _CACHE['local_ip']
    except Exception as e:
        logging.error('get_local_ip() failed %s', repr(e))
    return 'localhost'


async def get_public_ip() -> str:
    result = util.get('public_ip', _CACHE)
    if result:
        return result
    for url in ('https://api.seeip.org', 'https://api.ipify.org'):
        _CACHE['public_ip'] = await _fetch_text(url)
        if _CACHE['public_ip']:
            logging.debug('Public IP sourced from ' + url)
            return _CACHE['public_ip']
    _CACHE['public_ip'] = 'UNAVAILABLE'
    return _CACHE['public_ip']


async def _fetch_text(url: str) -> str | None:
    connector = aiohttp.TCPConnector(family=socket.AF_INET, force_close=True)
    timout = aiohttp.ClientTimeout(total=4.0)
    # noinspection PyBroadException
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timout) as session:
            async with session.get(url) as response:
                assert response.status == 200
                result = await response.text()
                return result.strip()
    except Exception as e:
        logging.warning('Failed to get public ip from %s because %s', url, repr(e))
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
    return '0.1.0 ({timestamp})'


async def system_info() -> dict:
    os_name, cpu, memory, disk, local_ip, public_ip = await asyncio.gather(
        get_os_name(), _cpu_percent(), _virtual_memory(), _disk_usage('/'), get_local_ip(), get_public_ip())
    return {
        'version': system_version(),
        'os': os_name,
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
