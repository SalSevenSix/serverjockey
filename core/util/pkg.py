import types
import pkgutil
import importlib
# ALLOW util.*
from core.util import funcutil

_import_module = funcutil.to_async(importlib.import_module)
_pkg_load = funcutil.to_async(pkgutil.get_data)


async def import_module(name: str) -> types.ModuleType:
    return await _import_module(name)


async def pkg_load(package: str, resource: str) -> bytes | None:
    return await _pkg_load(package, resource)
