import shutil
import psutil
from core.util import funcutil

_disk_usage = funcutil.to_async(shutil.disk_usage)
_virtual_memory = funcutil.to_async(psutil.virtual_memory)
_cpu_percent = funcutil.to_async(psutil.cpu_percent)


async def system_info() -> dict:
    disk = await _disk_usage('/')
    memory = await _virtual_memory()
    cpu = await _cpu_percent(1)
    return {
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
