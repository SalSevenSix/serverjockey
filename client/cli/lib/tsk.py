import logging
import inspect
import subprocess
# ALLOW lib.util
from . import util


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

    def _ctrld(self, argument: str):
        user, port = TaskProcessor._extract_user_and_port(argument)
        args = ' --port ' + str(port) if port != _DEFAULT_PORT else ''
        result = _serverjockey_service().format(user=user, args=args)
        self._dump_to_log(result)

    def _upgrade(self):
        result = subprocess.run(_upgrade_script().strip(), shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Upgrade task failed')

    def _uninstall(self):
        script = _uninstall_script().strip().replace('{userdef}', _DEFAULT_USER)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Uninstall task failed')

    def _adduser(self, argument: str):
        user, port = TaskProcessor._extract_user_and_port(argument)
        if user == 'serverjockey':
            raise Exception('User name not allowed')
        script = _adduser_script().strip()
        script = script.replace('{userdef}', _DEFAULT_USER).replace('{user}', user).replace('{port}', str(port))
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('New user task failed')

    def _userdel(self, argument: str):
        user = TaskProcessor._extract_user_and_port(argument)[0]
        if user == _DEFAULT_USER:
            raise Exception('Unable to delete default user.')
        script = _userdel_script().strip().replace('{user}', user)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Delete user task failed')

    # TODO Figure out proper way to launch editor
    def _serverlink_edit(self):
        script = _serverlink_edit_script().strip().replace('{user}', self._user)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('ServerLink Edit task failed')

    def _service(self, argument: str):
        args = argument + ' ' + ('serverjockey' if self._user == _DEFAULT_USER else self._user)
        script = _systemctl_script().strip().format(args=args)
        result = subprocess.run(script, shell=True, capture_output=True)
        self._dump_to_log(result.stdout, result.stderr)
        if result.returncode != 0:
            raise Exception('Service ' + argument + ' task failed')


def _serverjockey_service() -> str:
    return '''
[Unit]
Description=ServerJockey game server management system ({user})
Requires=network.target
After=network.target

[Service]
Type=simple
User={user}
ExecStart=/usr/local/bin/serverjockey.pyz --home "/home/{user}" --logfile{args}
KillMode=mixed
TimeoutStopSec=90
OOMScoreAdjust=-800

[Install]
WantedBy=multi-user.target
'''


def _systemctl_script() -> str:
    return '''
if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo."
  exit 1
fi
systemctl {args}
'''


def _upgrade_script() -> str:
    return '''
if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -t upgrade"
  exit 1
fi

INSTALLER="apt"
PKGTYPE="deb"
if which yum > /dev/null 2>&1; then
  INSTALLER="yum"
  PKGTYPE="rpm"
fi

rm sjgms.${PKGTYPE} > /dev/null 2>&1
wget --version > /dev/null 2>&1 || ${INSTALLER} -y install wget
echo "downloading..."
wget -q -O sjgms.${PKGTYPE} https://4sas.short.gy/sjgms-${PKGTYPE}-latest
[ $? -eq 0 ] || exit 1
${INSTALLER} -y install ./sjgms.${PKGTYPE}
[ $? -eq 0 ] || exit 1
rm sjgms.${PKGTYPE} > /dev/null 2>&1

echo "upgrade done"
exit 0
'''


def _adduser_script() -> str:
    return '''
if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -t adduser:<name>,<port>"
  exit 1
fi

SJGMS_USER_DEF="{userdef}"
SJGMS_USER="{user}"
SJGMS_PORT="{port}"
HOME_DIR="/home/$SJGMS_USER"
SERVERLINK_DIR="$HOME_DIR/serverlink"
SERVICE_NAME="$SJGMS_USER"
[ "$SJGMS_USER" = "$SJGMS_USER_DEF" ] && SERVICE_NAME="serverjockey"
id -u $SJGMS_USER_DEF > /dev/null 2>&1 || SERVICE_NAME="serverjockey"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

id -u $SJGMS_USER > /dev/null 2>&1
if [ $? -ne 0 ]; then
  rm -rf $HOME_DIR > /dev/null 2>&1
  adduser --system $SJGMS_USER || exit 1
  mkdir -p $SERVERLINK_DIR
  echo '{ "module": "serverlink", "auto": 3, "hidden": true }' > $SERVERLINK_DIR/instance.json
  find $HOME_DIR -type d -exec chmod 755 {} +
  find $HOME_DIR -type f -exec chmod 600 {} +
  chown -R $SJGMS_USER $HOME_DIR
  chgrp -R $(ls -ld $HOME_DIR | awk '{print $4}') $HOME_DIR
fi

[ -f $SERVICE_FILE ] || /usr/local/bin/serverjockey_cmd.pyz -nt ctrld:$SJGMS_USER,$SJGMS_PORT > $SERVICE_FILE
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo "adduser done"
exit 0
'''


def _serverlink_edit_script() -> str:
    return '''
CURRENT_USER="$(whoami)"
SJGMS_USER="{user}"
CONFIG_FILE="/home/$SJGMS_USER/serverlink/serverlink.json"
[ -f $CONFIG_FILE ] || CONFIG_FILE="/home/$SUDO_USER/serverlink/serverlink.json"
[ -f $CONFIG_FILE ] || CONFIG_FILE="/home/$SUDO_USER/serverjockey/serverlink/serverlink.json"
[ -f $CONFIG_FILE ] || CONFIG_FILE="/home/$CURRENT_USER/serverlink/serverlink.json"
[ -f $CONFIG_FILE ] || CONFIG_FILE="/home/$CURRENT_USER/serverjockey/serverlink/serverlink.json"
if [ ! -f $CONFIG_FILE ]; then
  echo "ServerLink config file not found."
  exit 1
fi

echo "sudo nano $CONFIG_FILE"
exit 0
'''


def _userdel_script() -> str:
    return '''
if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -t userdel:<name>"
  exit 1
fi

SJGMS_USER="{user}"
SERVICE_FILE="/etc/systemd/system/$SJGMS_USER.service"

if [ -f $SERVICE_FILE ]; then
  echo "removing service"
  systemctl stop $SJGMS_USER > /dev/null 2>&1
  rm $SERVICE_FILE > /dev/null 2>&1
  systemctl daemon-reload
fi

if id -u $SJGMS_USER > /dev/null 2>&1; then
  echo "removing user"
  userdel $SJGMS_USER
  rm -rf /home/$SJGMS_USER > /dev/null 2>&1
fi

echo "userdel done"
exit 0
'''


def _uninstall_script() -> str:
    return '''
if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -t uninstall"
  exit 1
fi

systemctl stop serverjockey > /dev/null 2>&1
which apt > /dev/null 2>&1 && apt -y remove {userdef}
which yum > /dev/null 2>&1 && yum -y remove {userdef}
systemctl daemon-reload
if id -u {userdef} > /dev/null 2>&1; then
  userdel {userdef}
  rm -rf /home/{userdef} > /dev/null 2>&1
fi

echo "uninstall done"
exit 0
'''
