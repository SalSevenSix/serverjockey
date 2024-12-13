import logging
import time
import os
import inspect
import subprocess
# ALLOW lib.util, lib.ddns
from . import util, cxt, ddns


def _checkpyz():
    if not os.path.isfile('/usr/local/bin/serverjockey_cmd.pyz'):
        raise Exception('Task not applicable when running from Source')


def _checkroot(args: str):
    script = util.get_resource('checkroot.sh').format(args=args)
    result = subprocess.run(script, shell=True, capture_output=True)
    _dump_to_log(result.stdout, result.stderr)
    if result.returncode != 0:
        raise Exception('Task not run')


def _extract_user_and_port(argument: str):
    user, port = util.split_argument(argument, 2)
    return user if user else util.DEFAULT_USER, int(port) if port else util.DEFAULT_PORT


def _dump_to_log(*data: str | bytes):
    if not data:
        return
    for item in data:
        text = item.decode() if isinstance(item, bytes) else item
        if text:
            for line in text.strip().split('\n'):
                logging.info(util.OUT + line)


class TaskProcessor:

    def __init__(self, context: cxt.Context):
        self._context, self._tasks = context, []
        for task in context.tasks():
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

    # noinspection PyMethodMayBeStatic
    def _sysdsvc(self, argument: str) -> bool:
        assert argument
        resource = util.get_resource('serverjockey.service')
        _dump_to_log(resource.format(user=argument))
        return True

    # noinspection PyMethodMayBeStatic
    def _pteroegg(self, argument: str) -> bool:
        assert argument
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) + '+00:00'
        resource = util.get_resource('pteroegg.json')
        resource = resource.replace('{version}', argument).replace('{timestamp}', timestamp)
        _dump_to_log(resource)
        return True

    # noinspection PyMethodMayBeStatic
    def _upgrade(self) -> bool:
        _checkpyz()
        _checkroot('upgrade')
        script = util.get_resource('upgrade.sh')
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Upgrade task failed')
        return True

    # noinspection PyMethodMayBeStatic
    def _uninstall(self) -> bool:
        _checkpyz()
        _checkroot('uninstall')
        script = util.get_resource('uninstall.sh').replace('{userdef}', util.DEFAULT_USER)
        result = subprocess.run(script, shell=True, capture_output=True)
        if result.returncode != 0:
            _dump_to_log(result.stdout, result.stderr)
            raise Exception('Uninstall task failed')
        return False

    # noinspection PyMethodMayBeStatic
    def _adduser(self, argument: str) -> bool:
        _checkpyz()
        _checkroot('adduser:<name>,<port>')
        user, port = _extract_user_and_port(argument)
        if user == util.DEFAULT_SERVICE:
            raise Exception('User name not allowed')
        script = util.get_resource('adduser.sh')
        script = script.replace('{userdef}', util.DEFAULT_USER).replace('{user}', user)
        script = script.replace('{portdef}', str(util.DEFAULT_PORT)).replace('{port}', str(port))
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('New user task failed')
        return True

    # noinspection PyMethodMayBeStatic
    def _userdel(self, argument: str) -> bool:
        _checkpyz()
        _checkroot('userdel:<name>')
        user = _extract_user_and_port(argument)[0]
        if user == util.DEFAULT_USER:
            raise Exception('Cannot delete default user. Use uninstall task instead.')
        script = util.get_resource('userdel.sh').replace('{user}', user)
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Delete user task failed')
        return True

    def _service(self, argument: str) -> bool:
        _checkpyz()
        _checkroot('service:<command>')
        user = self._context.user()
        args = argument if argument else 'status'
        args += ' '
        args += util.DEFAULT_SERVICE if user == util.DEFAULT_USER else user
        script = util.get_resource('systemctl.sh').format(args=args)
        result = subprocess.run(script, shell=True, capture_output=True)
        _dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Service ' + argument + ' task failed')
        return True

    def _wait(self, argument: str) -> bool:
        retries = util.to_int(argument, 0)
        if retries <= 0:
            return True
        while True:
            try:
                assert self._context.find_clientfile()  # just try find it first
                time.sleep(1.0)  # grace period
                assert self._context.credentials()  # now load to pre cache
                return True
            except Exception as e:
                if retries <= 0:
                    raise e
            retries -= 1
            time.sleep(1.0)

    # noinspection PyMethodMayBeStatic
    def _ddns(self, argument: str) -> bool:
        if not argument:
            _dump_to_log(util.get_resource('ddnshelp.text'))
            return True
        provider, = util.split_argument(argument, 1)
        if provider == 'duck':
            ddns.update_duck(*util.split_argument(argument, 3))
        elif provider == 'pork':
            ddns.update_pork(*util.split_argument(argument, 4))
        else:
            raise Exception('Unknown DDNS Service Provider')
        return True
