import types
import inspect
from core.util import util, pkg
from core.context import contextsvc
from core.system import svrabc

_MODULES = ('projectzomboid', 'factorio', 'sevendaystodie', 'unturned', 'starbound', 'csii', 'palworld')


class Modules:

    def __init__(self, context: contextsvc.Context):
        public_modules, all_modules = [], ['serverlink']
        if context.is_debug():
            public_modules.append('testserver')
        else:
            all_modules.append('testserver')
        public_modules.extend(_MODULES)
        all_modules.extend(public_modules)
        self._public_modules, self._all_modules = tuple(public_modules), tuple(all_modules)
        self._cache = {}

    def names(self) -> tuple:
        return self._public_modules

    def valid(self, module_name: str) -> bool:
        return module_name and module_name in self._all_modules

    async def create_server(self, subcontext: contextsvc.Context) -> svrabc.Server:
        module = await self._load(subcontext.config('module'))
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and svrabc.Server in inspect.getmro(member):
                return member(subcontext)
        raise Exception('Server class implementation not found in module: ' + repr(module))

    async def _load(self, module_name: str) -> types.ModuleType:
        assert self.valid(module_name)
        module = util.get(module_name, self._cache)
        if not module:
            module = await pkg.import_module('servers.' + module_name + '.server')
            self._cache[module_name] = module
        return module
