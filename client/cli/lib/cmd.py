import logging
import time
import inspect
# ALLOW lib.util, lib.comms
from . import util, comms


class CommandProcessor:

    def __init__(self, config: dict, connection: comms.HttpConnection):
        self._out, self._url, self._token = config['out'], config['url'], config['token']
        self._connection, self._commands, self._instance = connection, [], None
        self._instances: dict = connection.get('/instances')
        for command in config['commands']:
            argument, index = None, command.find(':')
            if index > 0:
                command, argument = command[:index], command[index + 1:]
            method_name = '_' + command.replace('-', '_')
            if hasattr(CommandProcessor, method_name):
                method = getattr(CommandProcessor, method_name)
                if callable(method):
                    entry = {'name': command, 'method': method}
                    if len(inspect.signature(method).parameters.keys()) > 1:
                        entry.update({'argument': argument})
                    self._commands.append(entry)
            else:
                raise Exception('Command {} not found'.format(command))

    def process(self):
        counter = 0
        for command in self._commands:
            counter += 1
            name, method = command['name'], command['method']
            prefix = '{:02d}> '.format(counter) if counter < 100 else '--> '
            if 'argument' in command:
                argument: str = command['argument']
                logging.info(prefix + name + (':' + argument if argument else ''))
                result = method(self, argument)
            else:
                logging.info(prefix + name)
                result = method(self)
            if not result:
                return

    def _instance_path(self, command_path: str) -> str:
        if not self._instance:
            if not self._use(None):
                raise Exception('_instance_path() was unable to find instance to use.')
        return '/instances/' + self._instance + command_path

    def _modules(self) -> bool:
        for module in self._connection.get('/modules'):
            logging.info(self._out + module)
        return True

    def _instances(self) -> bool:
        identities = self._instances.keys()
        if len(identities) == 0:
            logging.info('No instances found.')
            return True
        for identity in identities:
            logging.info(self._out + identity + ' ' + self._instances[identity]['module'])
        return True

    def _use(self, argument: str | None) -> bool:
        if argument:
            if argument == self._instance:
                return True
            if argument == 'serverlink' or argument in self._instances.keys():
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

    # TODO retest this
    def _create(self, argument: str | None) -> bool:
        instance, module = util.split_argument(argument, 2)
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

    def _runtime_meta(self) -> bool:
        result = self._connection.get(self._instance_path('/deployment/runtime-meta'))
        for line in result.split('\n'):
            logging.info(self._out + line)
        return True

    def _install_runtime(self, argument: str | None) -> bool:
        body = {'wipe': False, 'validate': True}
        if argument:
            body.update({'beta': argument})
        result = self._connection.post(self._instance_path('/deployment/install-runtime'), body)
        if result:
            self._connection.drain(result)
        return True

    def _wipe_runtime(self) -> bool:
        self._connection.post(self._instance_path('/deployment/wipe-runtime'))
        return True

    def _wipe_world_all(self) -> bool:
        self._connection.post(self._instance_path('/deployment/wipe-world-all'))
        return True

    def _wipe_world_save(self) -> bool:
        self._connection.post(self._instance_path('/deployment/wipe-world-save'))
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

    def _exit_if_players(self) -> bool:
        count = len(self._connection.get(self._instance_path('/players')))
        if count == 0:
            return True
        logging.info('exit-if-players command found players in-game, no more commands will be processed')
        return False

    def _exit_if_noplayers(self) -> bool:
        count = len(self._connection.get(self._instance_path('/players')))
        if count > 0:
            return True
        logging.info('exit-if-noplayers command found no players in-game, no more commands will be processed')
        return False

    # noinspection PyMethodMayBeStatic
    def _sleep(self, argument: str) -> bool:
        seconds = util.to_int(argument)
        if seconds:
            time.sleep(seconds)
        else:
            logging.warning('Invalid argument for sleep command, must be a number > 0, was: ' + str(argument))
        return True

    def _welcome(self) -> bool:
        logging.info(self._out)
        logging.info(self._out)
        logging.info(self._out + ' ===========================================================')
        logging.info(self._out + ' =                    WELCOME TO ZOMBOX                    =')
        logging.info(self._out + ' ===========================================================')
        logging.info(self._out)
        logging.info(self._out + ' Open the webapp then login with the token.')
        logging.info(self._out)
        logging.info(self._out + ' Address   ' + self._url.replace('localhost', util.get_ip()))
        logging.info(self._out + ' Token     ' + self._token)
        logging.info(self._out)
        return True

    def _showtoken(self) -> bool:
        logging.info(self._out + 'URL: ' + self._url.replace('localhost', util.get_ip()))
        logging.info(self._out + 'Token: ' + self._token)
        return True

    def _server(self) -> bool:
        result = self._connection.get(self._instance_path('/server'))
        result = 'instance: ' + self._instance + '\n' + util.repr_dict(result)
        for line in result.strip().split('\n'):
            logging.info(self._out + line)
        return True

    def _players(self) -> bool:
        result: list = self._connection.get(self._instance_path('/players'))
        logging.info(self._out + 'Players online: ' + str(len(result)))
        for player in result:
            line = self._out + player['name']
            if 'steamid' in player and player['steamid']:
                line += ' [' + player['steamid'] + ']'
            logging.info(line)
        return True

    def _system(self) -> bool:
        result = self._connection.get('/system/info')
        for line in util.repr_dict(result).strip().split('\n'):
            logging.info(self._out + line)
        return True

    def _report(self) -> bool:
        identities = self._instances.keys()
        if len(identities) == 0:
            return True
        original = self._instance
        for identity in identities:
            self._instance = identity
            result = self._connection.get(self._instance_path('/server'))
            for line in util.repr_dict(result, identity).strip().split('\n'):
                logging.info(self._out + line)
        self._instance = original
        return True

    def _log_tail(self, argument: str | None) -> bool:
        lines = util.to_int(argument) if argument else 100
        if not lines:
            lines = 100
            logging.warning('Invalid argument for log-tail command, must be a number > 0')
        result = self._connection.get(self._instance_path('/log/tail'))
        result = result.strip().split('\n')
        if len(result) > 0 and lines < 100:
            result = result[-lines:]
        for line in result:
            logging.info(self._out + line)
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

    def _backup_world(self, argument: str | None) -> bool:
        result = self._connection.post(
            self._instance_path('/deployment/backup-world'),
            {'prunehours': util.to_int_optional(argument)})
        self._connection.drain(result)
        return True

    def _backup_runtime(self, argument: str | None) -> bool:
        result = self._connection.post(
            self._instance_path('/deployment/backup-runtime'),
            {'prunehours': util.to_int_optional(argument)})
        self._connection.drain(result)
        return True

    def _shutdown(self) -> bool:
        self._connection.post('/system/shutdown')
        return False
