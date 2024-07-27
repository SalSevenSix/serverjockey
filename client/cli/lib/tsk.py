import logging
import os
import inspect
import subprocess
# ALLOW lib.util, lib.ddns
from . import util, ddns

_DEFAULT_SERVICE = 'serverjockey'
_DEFAULT_USER = 'sjgms'
_DEFAULT_PORT = 6164


def _checkpyz():
    if not os.path.isfile('/usr/local/bin/serverjockey_cmd.pyz'):
        raise Exception('Task not applicable when running from Source')


def _extract_user_and_port(argument: str):
    user, port = util.split_argument(argument, 2)
    return user if user else _DEFAULT_USER, int(port) if port else _DEFAULT_PORT


class TaskProcessor:

    def __init__(self, config: dict):
        self._out, self._tasks = config['out'], []
        self._user = config['user'] if config['user'] else _DEFAULT_USER
        for task in config['tasks']:
            argument, index = None, task.find(':')
            if index > 0:
                task, argument = task[:index], task[index + 1:]
            method_name = '_' + task.replace('-', '_')
            if hasattr(TaskProcessor, method_name):
                method = getattr(TaskProcessor, method_name)
                if callable(method):
                    entry = {'name': task, 'method': method}
                    if len(inspect.signature(method).parameters.keys()) > 1:
                        entry.update({'argument': argument})
                    self._tasks.append(entry)
            else:
                raise Exception('Task {} not found'.format(task))

    def process(self):
        for task in self._tasks:
            name, method = task['name'], task['method']
            if 'argument' in task:
                argument: str = task['argument']
                logging.info('--> ' + name + (':' + argument if argument else ''))
                result = method(self, argument)
            else:
                logging.info('--> ' + name)
                result = method(self)
            if not result:
                return

    def _dump_to_log(self, *data: str | bytes):
        if not data:
            return
        for item in data:
            text = item.decode() if isinstance(item, bytes) else item
            if text:
                for line in text.strip().split('\n'):
                    logging.info(self._out + line)

    def _checkroot(self, args: str):
        script = util.get_resource('checkroot.sh').format(args=args)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Task not run')

    def _sysdsvc(self, argument: str) -> bool:
        resource = util.get_resource('serverjockey.service')
        self._dump_to_log(resource.format(user=argument))
        return True

    def _upgrade(self) -> bool:
        _checkpyz()
        self._checkroot('upgrade')
        script = util.get_resource('upgrade.sh')
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Upgrade task failed')
        return True

    def _uninstall(self) -> bool:
        _checkpyz()
        self._checkroot('uninstall')
        script = util.get_resource('uninstall.sh').replace('{userdef}', _DEFAULT_USER)
        result = subprocess.run(script, shell=True, capture_output=True)
        if result.returncode != 0:
            self._dump_to_log(result.stdout, result.stderr)
            raise Exception('Uninstall task failed')
        return False

    def _adduser(self, argument: str) -> bool:
        _checkpyz()
        self._checkroot('adduser:<name>,<port>')
        user, port = _extract_user_and_port(argument)
        if user == _DEFAULT_SERVICE:
            raise Exception('User name not allowed')
        script = util.get_resource('adduser.sh')
        script = script.replace('{userdef}', _DEFAULT_USER).replace('{user}', user)
        script = script.replace('{portdef}', str(_DEFAULT_PORT)).replace('{port}', str(port))
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('New user task failed')
        return True

    def _userdel(self, argument: str) -> bool:
        _checkpyz()
        self._checkroot('userdel:<name>')
        user = _extract_user_and_port(argument)[0]
        if user == _DEFAULT_USER:
            raise Exception('Cannot delete default user. Use uninstall task instead.')
        script = util.get_resource('userdel.sh').replace('{user}', user)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Delete user task failed')
        return True

    def _service(self, argument: str) -> bool:
        _checkpyz()
        self._checkroot('service:<command>')
        args = argument if argument else 'status'
        args += ' '
        args += _DEFAULT_SERVICE if self._user == _DEFAULT_USER else self._user
        script = util.get_resource('systemctl.sh').format(args=args)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Service ' + argument + ' task failed')
        return True

    def _ddns(self, argument: str) -> bool:
        provider, = util.split_argument(argument, 1)
        if provider == 'help':
            for line in util.get_resource('ddnshelp.text').strip().split('\n'):
                logging.info(self._out + line)
        elif provider == 'duck':
            ddns.update_duck(*util.split_argument(argument, 3))
        elif provider == 'pork':
            ddns.update_pork(*util.split_argument(argument, 4))
        else:
            raise Exception('Unknown DDNS Service Provider')
        return True
