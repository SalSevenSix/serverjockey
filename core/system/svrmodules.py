import types
import inspect
# ALLOW util.* context.* system.svrabc
from core.util import util, pkg
from core.context import contextsvc
from core.system import svrabc

_MODULE_TESTSERVER, _MODULE_SERVERLINK = 'testserver', 'serverlink'
_MODULES = 'projectzomboid', 'factorio', 'sevendaystodie', 'unturned', 'starbound', 'csii', 'palworld', 'valheim'


class Modules:

    def __init__(self, context: contextsvc.Context):
        allowed_modules, single_instance = context.config('modules'), context.config('single')
        allowed_modules = [m for m in allowed_modules if m in _MODULES] if allowed_modules else _MODULES
        all_modules, public_modules = [], []
        if single_instance:
            all_modules.extend(allowed_modules)
            all_modules.extend([m for m in _MODULES if m not in allowed_modules])
        else:
            all_modules.extend(_MODULES)
            if context.is_debug():
                public_modules.append(_MODULE_TESTSERVER)
            public_modules.extend(allowed_modules)
        all_modules.append(_MODULE_TESTSERVER)
        all_modules.append(_MODULE_SERVERLINK)
        self._all_modules, self._public_modules = tuple(all_modules), tuple(public_modules)
        self._cache = {}

    def names(self) -> tuple:
        return self._public_modules

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
