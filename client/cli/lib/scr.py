import logging
import inspect
import subprocess


class ScriptProcessor:

    def __init__(self, config: dict):
        self._scripts = []
        for script in config['scripts']:
            argument, index = None, script.find(':')
            if index > 0:
                script, argument = script[:index], script[index + 1:]
            method_name = '_' + script.replace('-', '_')
            if hasattr(ScriptProcessor, method_name):
                method = getattr(ScriptProcessor, method_name)
                if callable(method):
                    entry = {'name': script, 'method': method}
                    if len(inspect.signature(method).parameters.keys()) > 1:
                        entry.update({'argument': argument})
                    self._scripts.append(entry)
            else:
                raise Exception('Script {} not found'.format(script))

    def process(self):
        for script in self._scripts:
            name, method = script['name'], script['method']
            if 'argument' in script:
                argument: str = script['argument']
                logging.info('--> ' + name + (':' + argument if argument else ''))
                result = method(self, argument)
            else:
                logging.info('--> ' + name)
                result = method(self)
            if not result:
                return

    def _upgrade(self):
        result = subprocess.run(_upgrade_script(), shell=True, capture_output=True)
        if result.stdout:
            for line in result.stdout.decode().strip().split('\n'):
                logging.info('    ' + line)
        if result.returncode != 0 or not result.stdout:
            raise Exception('Upgrade script failed')


def _upgrade_script() -> str:
    return '''
if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -s upgrade"
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
