import logging
# ALLOW util.util
from core.util import shellutil, io, tasks


async def _get_steamcmd_dir(home_dir: str) -> str | None:
    assert home_dir is not None
    steamcmd_dir = home_dir + '/.local/share/Steam/steamcmd'
    if not await io.directory_exists(steamcmd_dir):
        return None
    return steamcmd_dir


async def link_steamclient_to_sdk(home_dir: str):
    steamcmd_dir = await _get_steamcmd_dir(home_dir)
    if not steamcmd_dir:
        return
    sdk_dir = home_dir + '/.steam/sdk64'
    steamclient_link = sdk_dir + '/steamclient.so'
    if await io.symlink_exists(steamclient_link):
        return
    steamclient_file = steamcmd_dir + '/linux64/steamclient.so'
    if not await io.file_exists(steamclient_file):
        return
    await io.create_directories(sdk_dir)
    await io.create_symlink(steamclient_link, steamclient_file)


async def check_steam(home_dir: str):
    steamcmd_dir = await _get_steamcmd_dir(home_dir)
    if steamcmd_dir:
        return
    tasks.task_fork(_install_steam(), 'install_steam()')


async def _install_steam():
    logging.info('Installing SteamCMD for user')
    try:
        await shellutil.run_script('/usr/games/steamcmd +quit >/dev/null 2>&1')
        logging.info('SteamCMD install complete')
    except Exception as e:
        logging.warning('Exception installing SteamCMD: ' + repr(e))
