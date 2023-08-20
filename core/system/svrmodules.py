import types
import inspect
from core.util import util, pkg
from core.context import contextsvc
from core.system import svrabc

_TESTSERVER_MODULE = 'testserver'
_SERVERLINK_MODULE = 'serverlink'
_MODULES = ('projectzomboid', 'factorio', 'sevendaystodie', 'unturned', 'starbound')


class ModulesService:

    def __init__(self, context: contextsvc.Context):
        self._cache = {}
        modules = list(_MODULES)
        if context.is_debug():
            modules.append(_TESTSERVER_MODULE)
        self._public_modules = tuple(modules)
        modules.append(_SERVERLINK_MODULE)
        self._all_modules = tuple(modules)

    def names(self) -> tuple:
        return self._public_modules

    def valid(self, module_name: str) -> bool:
        return module_name and module_name in self._all_modules

    async def create_server(self, context: contextsvc.Context) -> svrabc.Server:
        module = await self._load(context.config('module'))
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and svrabc.Server in inspect.getmro(member):
                return member(context)
        raise Exception('Server class implementation not found in module: ' + repr(module))

    async def _load(self, module_name: str) -> types.ModuleType:
        assert self.valid(module_name)
        module = util.get(module_name, self._cache)
        if not module:
            module = await pkg.import_module('servers.' + module_name + '.server')
            self._cache[module_name] = module
        return module
