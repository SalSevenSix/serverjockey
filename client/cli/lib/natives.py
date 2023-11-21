import logging
import sys
import os
import shutil
import zipfile

# TODO depricated, delete sometime


def _find_packages_path():
    default_path = '/usr/local/lib/python3.10/dist-packages'
    if default_path in sys.path:
        return default_path
    for candidate in sys.path:
        if candidate.endswith('python3.10/dist-packages'):
            return candidate
    for candidate in sys.path:
        if candidate.endswith('/site-packages'):
            return candidate
    raise Exception('Unable to find suitable location')


def _check_installed(packages_path: str, modules: tuple) -> bool:
    found_modules = []
    for module in modules:
        if os.path.isdir(packages_path + '/' + module):
            found_modules.append(module)
    if len(found_modules) == len(modules):
        return True
    for module in found_modules:
        shutil.rmtree(packages_path + '/' + module)
    return False


def _find_modules(serverjockey_zipapp: str) -> tuple:
    modules, fd = [], None
    try:
        fd = zipfile.ZipFile(serverjockey_zipapp, mode='r')
        for path in fd.namelist():
            if path.startswith('___') and path.count('/') == 1 and path.endswith('/'):
                modules.append(path[3:-1])
        return tuple(modules)
    finally:
        if fd:
            fd.close()


def _unpack_modules(serverjockey_zipapp: str, packages_path: str, modules: tuple):
    fd, paths = None, []
    try:
        fd = zipfile.ZipFile(serverjockey_zipapp, mode='r')
        for path in fd.namelist():
            for module in modules:
                if path.startswith('___' + module + '/'):
                    paths.append(path)
        fd.extractall(path=packages_path, members=paths)
    finally:
        if fd:
            fd.close()


def _condition_modules(packages_path: str, modules: tuple):
    for module in modules:
        module_path = packages_path + '/' + module
        os.rename(packages_path + '/___' + module, module_path)
        for current_dir_path, subdir_names, file_names in os.walk(module_path):
            for file_name in file_names:
                os.chmod(os.path.join(current_dir_path, file_name), 0o644)


def _install():
    serverjockey_zipapp = '/usr/local/bin/serverjockey.pyz'
    if not os.path.isfile(serverjockey_zipapp):
        raise Exception(serverjockey_zipapp + ' not found')
    modules = _find_modules(serverjockey_zipapp)
    if len(modules) == 0:
        return
    packages_path = _find_packages_path()
    if not os.path.isdir(packages_path):
        os.makedirs(packages_path)
    if _check_installed(packages_path, modules):
        return
    _unpack_modules(serverjockey_zipapp, packages_path, modules)
    _condition_modules(packages_path, modules)


def install():
    try:
        _install()
    except Exception as e:
        logging.warning('Failed installing python modules with native libraries. ' + repr(e))
