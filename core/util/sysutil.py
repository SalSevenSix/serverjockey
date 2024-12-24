import logging
import shutil
import asyncio
import aiohttp
import socket
import time
# ALLOW util.*
from core.util import util, objconv, io, funcutil, shellutil, tasks

# TODO investigate using /proc data instead of executing programs

_disk_usage = funcutil.to_async(shutil.disk_usage)


def _grep_last_line(startswith: str, text: str | None) -> str | None:
    if not text:
        return None
    result = None
    for line in text.split('\n'):
        if line.startswith(startswith):
            result = line
    return result


async def _fetch_text(url: str) -> str | None:
    connector = aiohttp.TCPConnector(family=socket.AF_INET, force_close=True)
    timeout = aiohttp.ClientTimeout(total=4.0)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(url) as response:
                assert response.status == 200
                result = await response.text()
                return result.strip()
    except Exception as e:
        logging.warning('Failed to get public ip from %s because %s', url, repr(e))
    return None


class _OsName:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> str:
        file = '/etc/os-release'
        try:
            if await io.file_exists(file):
                data = await io.read_file(file)
                for line in data.split('\n'):
                    if line.startswith('PRETTY_NAME="'):
                        return line[13:-1]
        except Exception as e:
            logging.error('_OsName.get() failed %s', repr(e))
        return 'UNKNOWN'


class _LocalIp:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> str:
        try:
            result = await shellutil.run_executable('hostname', '-I')
            result = util.extract_hostname_ips(result)
            return result[0][0]  # first ipv4
        except Exception as e:
            logging.error('_LocalIp.get() failed %s', repr(e))
        return 'UNAVAILABLE'


class _PublicIp:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> str:
        for url in ('https://api.ipify.org', 'https://ipv4.seeip.org', 'https://ipinfo.io/ip'):
            result = await _fetch_text(url)
            if result:
                logging.debug('Public IP sourced from ' + url)
                return result
        return 'UNAVAILABLE'


class _DiskUsage:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> dict:
        result = await _disk_usage('/')
        return dict(total=result[0], used=result[1], free=result[2], percent=round((result[1] / result[0]) * 100.0, 1))


class _VirtualMemory:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> dict:
        result = dict(total=-1, used=-1, free=-1, available=-1, percent=-1)
        data = await shellutil.run_executable('free', '-b')
        line = _grep_last_line('Mem:', data)
        if line:
            line = line.strip().split(' ')
            line = [int(i) for i in line[1:] if i]
            result.update(dict(total=line[0], used=line[1], free=line[2], available=line[5],
                               percent=round((line[1] / line[0]) * 100.0, 1)))
        result['swap'] = None
        line = _grep_last_line('Swap:', data)
        if line:
            line = line.strip().split(' ')
            line = [int(i) for i in line[1:] if i]
            if line[0] > 0:
                result['swap'] = dict(total=line[0], used=line[1], free=line[2],
                                      percent=round((line[1] / line[0]) * 100.0, 1))
        return result


class _CpuPercent:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> float:
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


class _CpuInfo:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> dict:
        output = await shellutil.run_executable('lscpu')
        output = [o.strip() for o in output.split('\n')]
        result = dict(vendor='???', modelname='???', model='???', arch='???', sockets=0, cores=0, threads=0, cpus=0)
        for line in output:
            if line.startswith('Vendor ID:'):
                result['vendor'] = line[10:].strip()
            elif line.startswith('Model name:'):
                result['modelname'] = line[11:].strip()
            elif line.startswith('Model:'):
                result['model'] = line[6:].strip()
            elif line.startswith('Architecture:'):
                result['arch'] = line[13:].strip()
            elif line.startswith('Socket(s):'):
                result['sockets'] = objconv.to_int(line[10:].strip())
            elif line.startswith('Core(s) per socket:'):
                result['cores'] = objconv.to_int(line[19:].strip())
            elif line.startswith('Thread(s) per core:'):
                result['threads'] = objconv.to_int(line[19:].strip())
            elif line.startswith('CPU(s):'):
                result['cpus'] = objconv.to_int(line[7:].strip())
        return result


class _Cacher:

    def __init__(self, delegate, max_seconds: float):
        self._delegate, self._max_seconds = delegate, max_seconds
        self._task, self._value, self._updated = None, None, 0.0

    async def get(self):
        if self._task:
            await self._task
            return self._value
        if time.time() - self._updated > self._max_seconds:
            self._task = tasks.task_start(self._run(), self._delegate)
            await self._task
        return self._value

    async def _run(self):
        try:
            self._value = await self._delegate.get()
            self._updated = time.time()
        finally:
            tasks.task_end(self._task)
            self._task = None


_VERSION, _BUILDSTAMP = '0.16.0', '{timestamp}'
_VERSION_LABEL = _VERSION + ' (' + _BUILDSTAMP + ')'
_VERSION_DICT = dict(version=_VERSION, buildstamp=_BUILDSTAMP)
_OS_NAME = _Cacher(_OsName(), 31536000.0)
_LOCAL_IP = _Cacher(_LocalIp(), 31536000.0)
_PUBLIC_IP = _Cacher(_PublicIp(), 31536000.0)
_DISK_USAGE = _Cacher(_DiskUsage(), 120.0)
_VIRTUAL_MEMORY = _Cacher(_VirtualMemory(), 60.0)
_CPU_PERCENT = _Cacher(_CpuPercent(), 30.0)
_CPU_INFO = _Cacher(_CpuInfo(), 31536000.0)


def system_version() -> str:
    return _VERSION_LABEL


def system_version_dict() -> dict:
    return _VERSION_DICT


async def os_name() -> str:
    return await _OS_NAME.get()


async def local_ip() -> str:
    return await _LOCAL_IP.get()


async def public_ip() -> str:
    return await _PUBLIC_IP.get()


async def disk_usage() -> dict:
    return await _DISK_USAGE.get()


async def virtual_memory() -> dict:
    return await _VIRTUAL_MEMORY.get()


async def cpu_percent() -> float:
    return await _CPU_PERCENT.get()


async def cpu_info() -> dict:
    return await _CPU_INFO.get()


async def system_info() -> dict:
    # noinspection PyTypeChecker
    cpu, cpupct, os, disk, memory, local, public = await asyncio.gather(
        cpu_info(), cpu_percent(), os_name(), disk_usage(), virtual_memory(), local_ip(), public_ip())
    cpu['percent'], net = cpupct, dict(local=local, public=public)
    return dict(version=system_version(), os=os, cpu=cpu, memory=memory, disk=disk, net=net)
