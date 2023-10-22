import logging
import shutil
import asyncio
import aiohttp
import socket
# ALLOW util.*
from core.util import io, funcutil, shellutil, tasks


class _Cacher:
    __instance = None

    @staticmethod
    def instance():
        if not _Cacher.__instance:
            _Cacher.__instance = _Cacher()
        return _Cacher.__instance

    def __init__(self):
        self._data = {'os_name': {}, 'local_ip': {}, 'public_ip': {}}
        self._data['os_name']['task']: asyncio.Task | None = tasks.task_fork(self._get_os_name(), 'get_os_name()')
        self._data['local_ip']['task']: asyncio.Task | None = tasks.task_fork(self._get_local_ip(), 'get_local_ip()')
        self._data['public_ip']['task']: asyncio.Task | None = tasks.task_fork(self._get_public_ip(), 'get_public_ip()')

    async def get(self, item: str) -> str:
        data = self._data[item]
        if data['task']:
            await data['task']
        return data['value']

    async def _get_os_name(self):
        file = '/etc/os-release'
        self._data['os_name']['value'] = 'UNKNOWN'
        # noinspection PyBroadException
        try:
            if await io.file_exists(file):
                data = await io.read_file(file)
                for line in data.split('\n'):
                    if line.startswith('PRETTY_NAME="'):
                        self._data['os_name']['value'] = line[13:-1]
                        return
        except Exception as e:
            logging.error('_get_os_name() failed %s', repr(e))
        finally:
            self._data['os_name']['task'] = None

    async def _get_local_ip(self):
        self._data['local_ip']['value'] = 'localhost'
        # noinspection PyBroadException
        try:
            result = await shellutil.run_executable('hostname', '-I')
            self._data['local_ip']['value'] = result.strip().split()[0]
        except Exception as e:
            logging.error('_get_local_ip() failed %s', repr(e))
        finally:
            self._data['local_ip']['task'] = None

    async def _get_public_ip(self):
        self._data['public_ip']['value'] = 'UNAVAILABLE'
        try:
            for url in ('https://api.ipify.org', 'https://ipv4.seeip.org', 'https://ipinfo.io/ip'):
                result = await _Cacher._fetch_text(url)
                if result:
                    self._data['public_ip']['value'] = result
                    logging.debug('Public IP sourced from ' + url)
                    return
        finally:
            self._data['public_ip']['task'] = None

    @staticmethod
    async def _fetch_text(url: str) -> str | None:
        connector = aiohttp.TCPConnector(family=socket.AF_INET, force_close=True)
        timeout = aiohttp.ClientTimeout(total=4.0)
        # noinspection PyBroadException
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url) as response:
                    assert response.status == 200
                    result = await response.text()
                    return result.strip()
        except Exception as e:
            logging.warning('Failed to get public ip from %s because %s', url, repr(e))
        return None


async def get_os_name() -> str:
    return await _Cacher.instance().get('os_name')


async def get_local_ip() -> str:
    return await _Cacher.instance().get('local_ip')


async def get_public_ip() -> str:
    return await _Cacher.instance().get('public_ip')


_disk_usage = funcutil.to_async(shutil.disk_usage)


def _grep_last_line(startswith: str, text: str | None) -> str | None:
    if not text:
        return None
    result = None
    for line in text.split('\n'):
        if line.startswith(startswith):
            result = line
    return result


async def _virtual_memory() -> tuple:
    result = await shellutil.run_executable('free', '-b')
    result = _grep_last_line('Mem:', result)
    if not result:
        return -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
    result = result.strip().split(' ')
    result.pop(0)
    result = [int(i) for i in result if i]
    result = [result[0], result[5], round(float(result[1] / result[0] * 100), 1),
              result[1], result[2], -1, -1, -1, result[4], -1, -1]
    return tuple(result)


async def _cpu_percent() -> float:
    result = await shellutil.run_executable('top', '-b', '-n', '2')
    result = _grep_last_line('%Cpu(s)', result)
    if not result:
        return 0.0
    result = result.strip().split(' ')
    result = [i for i in result if i]
    result = result[result.index('id,') - 1]
    if result == 'ni,100.0':
        return 0.0
    return round(100.0 - float(result), 1)


def system_version() -> str:
    return '0.5.0 ({timestamp})'


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
