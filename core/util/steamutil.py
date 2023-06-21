import logging
# ALLOW util.util
from core.util import shellutil, io, tasks

# TODO This should be in core.common.steam but don't want to reference that in core.system.boostrap


async def check_steam(home_dir: str):
    if not home_dir:
        return
    if await io.directory_exists(home_dir + '/Steam'):
        return
    tasks.task_fork(_install_steam(), 'Steam Installer')


async def _install_steam():
    logging.info('Installing Steam for user')
    try:
        await shellutil.run_script('/usr/games/steamcmd +quit >/dev/null 2>&1')
    except Exception as e:
        logging.warning('Failed installing Steam: ' + repr(e))
        return
    logging.info('Steam install complete')
