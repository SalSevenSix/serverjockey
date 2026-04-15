import logging
import time
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


class _SteamCmdFinder:

    def __init__(self):
        self._steamcmd_exe, self._last = 'steamcmd', 0.0

    async def initialise(self, home_dir: str, env_paths: str) -> bool:
        paths = '/usr/games:/usr/bin'
        if env_paths:
            paths += ':' + env_paths
        steamcmd_exe = await io.find_in_env_path(paths, 'steamcmd')
        if not steamcmd_exe and await io.file_exists(home_dir + '/Steam/steamcmd.sh'):
            steamcmd_exe = '~/Steam/steamcmd.sh'
        self._steamcmd_exe = steamcmd_exe if steamcmd_exe else '$(pwd)/steamcmd.sh'
        return bool(steamcmd_exe)

    def script_refresh(self) -> str:
        return self._steamcmd_exe + ' +quit >/dev/null 2>&1'

    def script_execute(self) -> str:
        script, now = self._steamcmd_exe, time.time()
        if now - self._last > 3600.0:  # 1 hour
            script = self.script_refresh() + '\nsleep 1\n' + script
            self._last = now
        return script


_STEAMCMD_FINDER = _SteamCmdFinder()


async def ensure_steamcmd(home_dir: str, env_paths: str):
    steamcmd_dir = await get_steamcmd_dir(home_dir)
    if steamcmd_dir:
        logging.info('SteamCMD: %s', steamcmd_dir)
    found_steamcmd_exe = await _STEAMCMD_FINDER.initialise(home_dir, env_paths)
    if not found_steamcmd_exe:
        logging.warning('SteamCMD executable not found')
    if steamcmd_dir or not found_steamcmd_exe:
        return
    logging.info('SteamCMD installing for service user')
    try:
        await shellutil.run_script(_STEAMCMD_FINDER.script_refresh())
        logging.info('SteamCMD install completed')
    except Exception as e:
        logging.warning('SteamCMD install exception: %s', repr(e))


def steamcmd_script() -> str:
    return _STEAMCMD_FINDER.script_execute()
