import logging
import inspect
import subprocess


class TaskProcessor:

    def __init__(self, config: dict):
        self._out, self._tasks = config['out'], []
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

    def _ctrld(self, argument: str):
        user, port = 'sjgms', None
        if argument:
            parts = argument.split(',')
            user, port = parts[0], int(parts[1]) if len(parts) > 1 else None
        args = ' --port ' + str(port) if port else ''
        result = _serverjockey_service().format(user=user, args=args)
        for line in result.strip().split('\n'):
            logging.info(self._out + line)

    def _upgrade(self):
        result = subprocess.run(_upgrade_script().strip(), shell=True, capture_output=True)
        if result.stdout:
            for line in result.stdout.decode().strip().split('\n'):
                logging.info(self._out + line)
        if result.returncode != 0 or not result.stdout:
            raise Exception('Upgrade task failed')


def _serverjockey_service() -> str:
    return '''
[Unit]
Description=ServerJockey game server management system ({user})
Requires=network.target
After=network.target

[Service]
Type=simple
User={user}
ExecStart=/usr/local/bin/serverjockey.pyz --home "/home/{user}" --logfile "serverjockey.log"{args}
KillMode=mixed
TimeoutStopSec=90
OOMScoreAdjust=-800

[Install]
WantedBy=multi-user.target
'''


def _upgrade_script() -> str:
    return '''
if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -t upgrade"
  exit 1
fi
if which yum > /dev/null; then
  INSTALLER="yum"
  PKGTYPE="rpm"
fi
if which apt > /dev/null; then
  INSTALLER="apt"
  PKGTYPE="deb"
fi
if [ -z "${INSTALLER}" ]; then
  echo "Unable to identify package installer. Only apt and yum supported."
  exit 1
fi
echo "Upgrading ServerJockey..."
rm sjgms.${PKGTYPE} > /dev/null 2>&1
wget --version > /dev/null 2>&1 || apt -y install wget
echo "Downloading"
wget -q -O sjgms.${PKGTYPE} https://4sas.short.gy/sjgms-${PKGTYPE}-latest
[ $? -eq 0 ] || exit 1
echo "Installing"
${INSTALLER} -y install ./sjgms.${PKGTYPE} 2>&1
[ $? -eq 0 ] || exit 1
rm sjgms.${PKGTYPE} > /dev/null 2>&1
echo "Upgrade complete"
exit 0
'''
