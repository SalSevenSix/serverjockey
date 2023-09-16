import types
import inspect
from core.util import util, pkg
from core.context import contextsvc
from core.system import svrabc

# TODO Consider pulling this list from meta data under servers package, maybe use init.py files
_PUBLIC_MODULES = ('projectzomboid', 'factorio', 'sevendaystodie', 'unturned', 'starbound', 'csgo')
_ALL_MODULES = _PUBLIC_MODULES + ('serverlink', 'testserver')


class Modules:

    def __init__(self):
        self._cache = {}

    @staticmethod
    def names() -> tuple:
        return _PUBLIC_MODULES

    @staticmethod
    def valid(module_name: str) -> bool:
        return module_name and module_name in _ALL_MODULES

    async def create_server(self, context: contextsvc.Context) -> svrabc.Server:
        module = await self._load(context.config('module'))
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and svrabc.Server in inspect.getmro(member):
                return member(context)
        raise Exception('Server class implementation not found in module: ' + repr(module))

    async def _load(self, module_name: str) -> types.ModuleType:
        assert Modules.valid(module_name)
        module = util.get(module_name, self._cache)
        if not module:
            module = await pkg.import_module('servers.' + module_name + '.server')
            self._cache[module_name] = module
        return module
