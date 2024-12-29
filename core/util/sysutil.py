import logging
import shutil
import asyncio
import aiohttp
import socket
import time
# ALLOW util.*
from core.util import util, objconv, io, funcutil, shellutil, tasks


_disk_usage = funcutil.to_async(shutil.disk_usage)


async def _get_cpu_idle() -> float:
    result, cpus, stats = None, 0, await io.read_file('/proc/stat')
    for line in stats.split('\n'):
        if line.startswith('cpu'):
            if line[3] == ' ':
                result = int(line[4:].strip().split(' ')[3])
            else:
                cpus += 1
    if result is None:
        raise Exception('get_cpu_idle() failed')
    return result / (100.0 * (cpus if cpus else 1.0))


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
        data = await _disk_usage('/')
        return dict(total=data[0], used=data[1], free=data[2], percent=round((data[1] / data[0]) * 100.0, 1))


class _VirtualMemory:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> dict:
        result = dict(total=0, used=0, free=0, available=0, percent=0.0)
        result['swap'] = None
        meminfo = await shellutil.run_executable('free', '-b')
        for line in meminfo.split('\n'):
            if line.startswith('Mem:'):
                data = [int(i) for i in line.strip().split(' ')[1:] if i]
                result.update(dict(total=data[0], used=data[1], free=data[2], available=data[5],
                                   percent=round((data[1] / data[0]) * 100.0, 1)))
            elif line.startswith('Swap:'):
                data = [int(i) for i in line.strip().split(' ')[1:] if i]
                if data[0] > 0:
                    result['swap'] = dict(total=data[0], used=data[1], free=data[2],
                                          percent=round((data[1] / data[0]) * 100.0, 1))
        return result


class _CpuPercent:
    def __init__(self, min_duration: float, max_duration: float):
        self._min_duration, self._max_duration = min_duration, max_duration
        self._last_time, self._last_idle = 0.0, None

    async def get(self) -> float:
        last_idle, now = self._last_idle, time.time()
        wait, duration = 0.0, now - self._last_time
        if duration > self._max_duration:
            wait, last_idle = self._min_duration, await _get_cpu_idle()
        elif duration < self._min_duration:
            wait = self._min_duration - duration
        if wait > 0.0:
            await asyncio.sleep(wait)
            duration, now = self._min_duration, now + wait
        this_idle = await _get_cpu_idle()
        result = (duration - (this_idle - last_idle)) / duration
        result = result if result > 0.0 else 0.0
        result = result if result < 1.0 else 1.0
        self._last_time, self._last_idle = now, this_idle
        return round(result * 100.0, 1)


class _CpuInfo:
    # noinspection PyMethodMayBeStatic
    async def get(self) -> dict:
        result = dict(vendor='???', modelname='???', model='???', arch='???', sockets=0, cores=0, threads=0, cpus=0)
        data = await shellutil.run_executable('lscpu')
        data = [o.strip() for o in data.split('\n')]
        for line in data:
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
_CPU_PERCENT = _Cacher(_CpuPercent(1.0, 15.0), 10.0)
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
