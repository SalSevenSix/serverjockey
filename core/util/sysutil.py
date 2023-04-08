import shutil
import asyncio
from core.util import __version__, funcutil, shellutil


_disk_usage = funcutil.to_async(shutil.disk_usage)
# _virtual_memory = funcutil.to_async(psutil.virtual_memory)
# _cpu_percent = funcutil.to_async(psutil.cpu_percent)


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
    cpu, memory, disk = await asyncio.gather(_cpu_percent(), _virtual_memory(), _disk_usage('/'))
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
        }
    }
