import logging
import types
import inspect
# ALLOW util.* context.* system.svrabc
from core.util import util, pkg
from core.context import contextsvc
from core.system import svrabc

_MODULE_TESTSERVER, _MODULE_SERVERLINK = 'testserver', 'serverlink'
_MODULE_DATA = dict(
    projectzomboid='Project Zomboid',
    factorio='Factorio',
    sevendaystodie='7 Days to Die',
    unturned='Unturned',
    starbound='Starbound',
    palworld='Palworld',
    valheim='Valheim',
    csii='Counter Strike 2',
    teamspeak='TeamSpeak 3')


class Modules:

    def __init__(self, context: contextsvc.Context):
        modules, allowed_modules, single = _MODULE_DATA.keys(), context.config('modules'), context.config('single')
        allowed_modules = [m for m in allowed_modules if m in modules] if allowed_modules else modules
        all_modules, public_modules = [], []
        if single:
            all_modules.extend(allowed_modules)
            all_modules.extend([m for m in modules if m not in allowed_modules])
        else:
            all_modules.extend(modules)
            if context.is_debug():
                public_modules.append(_MODULE_TESTSERVER)
            public_modules.extend(allowed_modules)
        all_modules.append(_MODULE_TESTSERVER)
        all_modules.append(_MODULE_SERVERLINK)
        if single:
            logging.info('Instance: %s (%s)', single, all_modules[0])
        else:
            logging.info('Modules: %s', ','.join(public_modules))
        self._all_modules, self._public_modules = tuple(all_modules), tuple(public_modules)
        self._cache = {}

    def modules(self) -> dict:
        result = util.filter_dict(_MODULE_DATA, self._public_modules)
        if _MODULE_TESTSERVER in self._public_modules:
            result[_MODULE_TESTSERVER] = _MODULE_TESTSERVER
        return result

    def default_name(self) -> str:
        return self._all_modules[0]

    def supported(self, module_name: str) -> bool:
        return module_name and module_name in self._all_modules

    def can_create(self, module_name: str) -> bool:
        return module_name and module_name in self._public_modules

    async def create_server(self, subcontext: contextsvc.Context) -> svrabc.Server:
        module = await self._load(subcontext.config('module'))
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and svrabc.Server in inspect.getmro(member):
                return member(subcontext)
        raise Exception('Server class implementation not found in module: ' + repr(module))

    async def _load(self, module_name: str) -> types.ModuleType:
        assert self.supported(module_name)
        module = util.get(module_name, self._cache)
        if not module:
            module = await pkg.import_module('servers.' + module_name + '.server')
            self._cache[module_name] = module
        return module
