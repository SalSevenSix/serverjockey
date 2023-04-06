import logging
import time
import inspect
from . import util, comms

_OUT = '    '


def epilog() -> str:
    return '''
        COMMANDS: instances modules use:"<instance>" create:"<instance>,<module>" delete install-runtime:"<version>"
        exit-if-down exit-if-up sleep:<duration> server server-daemon server-start server-restart server-stop
        console-send:"<cmd>" world-broadcast:"<message>" backup-world:<prunehours> backup-runtime:<prunehours>
        log-tail:<lines> log-tail-f
    '''


def _get_prune_hours(argument: str) -> int:
    prune_hours = 0
    if argument:
        prune_hours = util.to_int(argument)
        if prune_hours is None:
            prune_hours = 0
            logging.warning('Invalid argument for prune hours, must be a number, was: ' + str(argument))
    return prune_hours


class CommandProcessor:

    def __init__(self, config: dict, connection: comms.HttpConnection):
        self._connection = connection
        self._instances: dict = self._connection.get('/instances')
        self._instance = None
        self._commands = []
        for command in config['commands']:
            argument, index = None, command.find(':')
            if index > 0:
                command, argument = command[:index], command[index + 1:]
            method_name = '_' + command.replace('-', '_')
            if hasattr(CommandProcessor, method_name):
                method = getattr(CommandProcessor, method_name)
                if callable(method):
                    if len(inspect.signature(method).parameters.keys()) > 1:
                        self._commands.append({'method': method, 'argument': argument})
                    else:
                        self._commands.append({'method': method})
            else:
                raise Exception('Command {} not found'.format(command))

    def process(self):
        counter = 0
        for command in self._commands:
            counter += 1
            method = command['method']
            logging.info(str(counter) + ' : ' + str(method))
            if 'argument' in command:
                result = method(self, command['argument'])
            else:
                result = method(self)
            if not result:
                return

    def _instance_path(self, command_path: str) -> str:
        if not self._instance:
            if not self._use(None):
                raise Exception('_instance_path() was unable to find instance to use.')
        return '/instances/' + self._instance + command_path

    def _modules(self) -> bool:
        logging.info('Modules...')
        for module in self._connection.get('/modules'):
            logging.info(_OUT + module)
        return True

    def _instances(self) -> bool:
        identities = self._instances.keys()
        if len(identities) == 0:
            logging.info('No instances found.')
            return True
        logging.info('Instances...')
        for identity in identities:
            prefix = ' => ' if identity == self._instance else _OUT
            logging.info(prefix + identity + ' (' + self._instances[identity]['module'] + ')')
        return True

    def _use(self, argument: str | None) -> bool:
        if argument:
            if argument in self._instances.keys():
                self._instance = argument
                logging.info('Instance set to: ' + self._instance)
                return True
            logging.error('Instance ' + argument + ' does not exist. No more commands will be processed.')
            return False
        if len(self._instances) > 0:
            self._instance = list(self._instances.keys())[0]
            logging.info('Instance defaulted to: ' + self._instance)
            return True
        logging.error('No instances found. No more commands will be processed.')
        return False

    def _create(self, argument: str) -> bool:
        if not argument:
            argument = ','
        parts, instance, module = argument.split(','), None, None
        if len(parts) >= 2:
            instance, module = parts[0], parts[1]
        if not instance or not module:
            logging.error('Instance name and module required. No more commands will be processed.')
            return False
        if instance in self._instances.keys():
            logging.error('Instance already exists. No more commands will be processed.')
            return False
        if module not in self._connection.get('/modules'):
            logging.error('Module not found. No more commands will be processed.')
            return False
        logging.info('Creating instance: ' + instance + ' (' + module + ')')
        self._connection.post('/instances', {'module': module, 'identity': instance})
        self._instances.update({instance: {'module': module}})
        self._use(instance)
        return True

    def _install_runtime(self, argument: str) -> bool:
        body = {'wipe': False, 'validate': True}
        if argument:
            body.update({'beta': argument})
        result = self._connection.post(self._instance_path('/deployment/install-runtime'), body)
        if result:
            self._connection.drain(result)
        return True

    def _delete(self) -> bool:
        if not self._instance:
            logging.error('Instance must be explicitly set to delete. No more commands will be processed.')
            return False
        self._connection.post(self._instance_path('/server/delete'))
        logging.info('Deleted instance: ' + self._instance)
        del self._instances[self._instance]
        self._instance = None
        return True

    def _exit_if_down(self) -> bool:
        status = self._connection.get(self._instance_path('/server'))
        if status['running']:
            return True
        logging.info('exit-if-down command found the server down, no more commands will be processed')
        return False

    def _exit_if_up(self) -> bool:
        status = self._connection.get(self._instance_path('/server'))
        if not status['running']:
            return True
        logging.info('exit-if-up command found the server up, no more commands will be processed')
        return False

    # noinspection PyMethodMayBeStatic
    def _sleep(self, argument: str) -> bool:
        seconds = util.to_int(argument)
        if seconds:
            time.sleep(seconds)
        else:
            logging.warning('Invalid argument for sleep command, must be a number > 0, was: ' + str(argument))
        return True

    def _server(self) -> bool:
        result = self._connection.get(self._instance_path('/server'))
        logging.info(_OUT + str(result))
        return True

    def _log_tail(self, argument: str) -> bool:
        lines = util.to_int(argument) if argument else 100
        if not lines:
            lines = 100
            logging.warning('Invalid argument for log-tail command, must be a number > 0')
        result = self._connection.get(self._instance_path('/log/tail'))
        result = result.strip().split('\n')
        if len(result) > 0 and lines < 100:
            result = result[-lines:]
        for line in result:
            logging.info(_OUT + line)
        return True

    def _log_tail_f(self) -> bool:
        self._log_tail('10')
        result = self._connection.post(self._instance_path('/log/subscribe'))
        self._connection.drain(result)
        return True

    def _server_daemon(self) -> bool:
        self._connection.post(self._instance_path('/server/daemon'))
        return True

    def _server_start(self) -> bool:
        self._connection.post(self._instance_path('/server/start'))
        return True

    def _server_restart(self) -> bool:
        self._connection.post(self._instance_path('/server/restart'))
        return True

    def _server_stop(self) -> bool:
        self._connection.post(self._instance_path('/server/stop'))
        return True

    def _console_send(self, argument: str) -> bool:
        self._connection.post(self._instance_path('/console/send'), {'line': str(argument)})
        return True

    def _world_broadcast(self, argument: str) -> bool:
        self._connection.post(self._instance_path('/world/broadcast'), {'message': str(argument)})
        return True

    def _backup_world(self, argument: str) -> bool:
        result = self._connection.post(
            self._instance_path('/deployment/backup-world'),
            {'prunehours': _get_prune_hours(argument)})
        self._connection.drain(result)
        return True

    def _backup_runtime(self, argument: str) -> bool:
        result = self._connection.post(
            self._instance_path('/deployment/backup-runtime'),
            {'prunehours': _get_prune_hours(argument)})
        self._connection.drain(result)
        return True
