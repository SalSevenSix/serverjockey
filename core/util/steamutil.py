import logging
# ALLOW util.util
from core.util import shellutil, io

# SteamCMD Paths Used...
#   ~/.local/share/Steam/steamcmd /linux64/steamclient.so  ~/Steam /linux64/steamclient.so
#   ~/.local/share/Steam/config/config.vdf  ~/Steam/config/config.vdf
# Ubuntu 22 Normal SteamCMD
#   exists ~/.local/share/Steam/steamcmd/linux64/steamclient.so
#   exists ~/Steam/config/config.vdf
#   both ~/.local/share/Steam/steamcmd and ~/Steam
#   no ~/.local/share/Steam/config
# Ubuntu 22 Manual SteamCMD
#   exists ~/Steam/linux64/steamclient.so
#   exists ~/Steam/config/config.vdf
#   no ~/.local/share/Steam/steamcmd
# Ubuntu 24 Normal SteamCMD
#   exists ~/.local/share/Steam/steamcmd/linux64/steamclient.so
#   exists ~/.local/share/Steam/config/config.vdf
#   no ~/Steam but ~/.steam
# Ubuntu 24 Manual SteamCMD
#   exists ~/Steam/linux64/steamclient.so
#   exists ~/Steam/config/config.vdf
#   no ~/.local/share/Steam/steamcmd


async def get_config_path(home_dir: str) -> str:
    for path in (home_dir + '/.local/share/Steam/config/config.vdf', home_dir + '/Steam/config/config.vdf'):
        if await io.file_exists(path):
            return path
    raise Exception('Steam config file not found.')


async def get_steamcmd_dir(home_dir: str) -> str | None:
    for path in (home_dir + '/.local/share/Steam/steamcmd', home_dir + '/Steam'):
        if await io.directory_exists(path):
            return path
    return None


async def link_steamclient_to_sdk(home_dir: str):
    steamcmd_dir = await get_steamcmd_dir(home_dir)
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
    steamcmd_dir = await get_steamcmd_dir(home_dir)
    if steamcmd_dir:
        logging.info('SteamCMD: %s', steamcmd_dir)
        return
    steamcmd_exe = '/usr/games/steamcmd'
    if not await io.file_exists(steamcmd_exe):
        logging.warning('%s not found, unable to install SteamCMD for user', steamcmd_exe)
        return
    logging.info('Installing SteamCMD into %s', home_dir)
    try:
        await shellutil.run_script(steamcmd_exe + ' +quit >/dev/null 2>&1')
        logging.info('SteamCMD install completed')
    except Exception as e:
        logging.warning('Exception installing SteamCMD: %s', repr(e))
