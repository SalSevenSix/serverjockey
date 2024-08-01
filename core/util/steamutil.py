import logging
# ALLOW util.util
from core.util import shellutil, io


async def _get_steamcmd_dir(home_dir: str) -> str | None:
    for path in (home_dir + '/.local/share/Steam/steamcmd', home_dir + '/Steam'):
        if await io.directory_exists(path):
            return path
    return None


async def link_steamclient_to_sdk(home_dir: str):
    steamcmd_dir = await _get_steamcmd_dir(home_dir)
    if not steamcmd_dir:
        return  # silent fail
    sdk_dir = home_dir + '/.steam/sdk64'
    steamclient_link = sdk_dir + '/steamclient.so'
    if await io.symlink_exists(steamclient_link):
        return
    steamclient_file = steamcmd_dir + '/linux64/steamclient.so'
    if not await io.file_exists(steamclient_file):
        return
    await io.create_directories(sdk_dir)
    await io.create_symlink(steamclient_link, steamclient_file)


async def ensure_steamcmd(home_dir: str):
    steamcmd_dir = await _get_steamcmd_dir(home_dir)
    if steamcmd_dir:
        logging.info('SteamCMD: ' + steamcmd_dir)
        return
    steamcmd_exe = '/usr/games/steamcmd'
    if not await io.file_exists(steamcmd_exe):
        logging.warning(steamcmd_exe + ' not found, unable to install SteamCMD for user')
        return
    logging.info('Installing SteamCMD in ' + home_dir)
    try:
        await shellutil.run_script(steamcmd_exe + ' +quit >/dev/null 2>&1')
        logging.info('SteamCMD install completed')
    except Exception as e:
        logging.warning('Exception installing SteamCMD: ' + repr(e))
