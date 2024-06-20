import logging
import inspect
import subprocess
# ALLOW lib.util, lib.ddns
from . import util, ddns

_DEFAULT_USER = 'sjgms'
_DEFAULT_PORT = 6164


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

    @staticmethod
    def _extract_user_and_port(argument: str):
        user, port = util.split_argument(argument, 2)
        return user if user else _DEFAULT_USER, int(port) if port else _DEFAULT_PORT

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

    def _sysdsvc(self, argument: str):
        user, port = TaskProcessor._extract_user_and_port(argument)
        args = ' --port ' + str(port) if port != _DEFAULT_PORT else ''
        result = util.get_resource('serverjockey.service').format(user=user, args=args)
        self._dump_to_log(result)

    def _upgrade(self):
        self._checkroot('upgrade')
        script = util.get_resource('upgrade.sh')
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Upgrade task failed')

    def _uninstall(self):
        self._checkroot('uninstall')
        script = util.get_resource('uninstall.sh').replace('{userdef}', _DEFAULT_USER)
        result = subprocess.run(script, shell=True, capture_output=True)
        if result.returncode != 0:
            self._dump_to_log(result.stdout, result.stderr)
            raise Exception('Uninstall task failed')

    def _adduser(self, argument: str):
        self._checkroot('adduser:<name>,<port>')
        user, port = TaskProcessor._extract_user_and_port(argument)
        if user == 'serverjockey':
            raise Exception('User name not allowed')
        script = util.get_resource('adduser.sh')
        script = script.replace('{userdef}', _DEFAULT_USER).replace('{user}', user).replace('{port}', str(port))
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('New user task failed')

    def _userdel(self, argument: str):
        self._checkroot('userdel:<name>')
        user = TaskProcessor._extract_user_and_port(argument)[0]
        if user == _DEFAULT_USER:
            raise Exception('Unable to delete default user.')
        script = util.get_resource('userdel.sh').replace('{user}', user)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Delete user task failed')

    def _service(self, argument: str):
        self._checkroot('service:<command>')
        args = argument if argument else 'status'
        args += ' '
        args += 'serverjockey' if self._user == _DEFAULT_USER else self._user
        script = util.get_resource('systemctl.sh').format(args=args)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Service ' + argument + ' task failed')

    def _ddns(self, argument: str):
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
