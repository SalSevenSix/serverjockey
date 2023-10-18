import logging
# ALLOW util.util
from core.util import shellutil, io, tasks


async def link_steamclient_to_sdk(home_dir: str):
    if not home_dir:
        return
    steam_dir = home_dir + '/.steam'
    sdk_dir = steam_dir + '/sdk64'
    steamclient_link = sdk_dir + '/steamclient.so'
    if await io.symlink_exists(steamclient_link):
        return
    if not await io.directory_exists(steam_dir):
        return
    steamclient_file = home_dir + '/.local/share/Steam/steamcmd/linux64/steamclient.so'
    if not await io.file_exists(steamclient_file):
        return
    await io.create_directory(sdk_dir)
    await io.create_symlink(steamclient_link, steamclient_file)


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
        logging.info('Steam install complete')
    except Exception as e:
        logging.warning('Failed installing Steam: ' + repr(e))
