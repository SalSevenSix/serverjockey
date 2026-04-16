import logging
import time
# ALLOW util.util
from core.util import shellutil, io

# Manual SteamCMD install
#   Script: ~/Steam/steamcmd.sh
#   Config: ~/Steam/config/config.vdf
#   Binary: ~/Steam/linux64/steamclient.so
# Ubuntu 22 Normal SteamCMD
#   Launch: /usr/games/steamcmd
#   Script: ~/.local/share/Steam/steamcmd/steamcmd.sh
#   Config: ~/Steam/config/config.vdf
#   Binary: ~/.local/share/Steam/steamcmd/linux64/steamclient.so
#     both exist: ~/.local/share/Steam/steamcmd and ~/Steam
#     exists but no config file: ~/.local/share/Steam/.steam/config
# Ubuntu 24 Normal SteamCMD
#   Launch: /usr/games/steamcmd
#   Script: ~/.local/share/Steam/steamcmd/steamcmd.sh
#   Config: ~/.local/share/Steam/config/config.vdf
#   Binary: ~/.local/share/Steam/steamcmd/linux64/steamclient.so
#     both exist: ~/.local/share/Steam/steamcmd and ~/.steam
# CachyOS Normal SteamCMD
#   Launch: /usr/bin/steamcmd
#   Script: ~/.steam/steamcmd/steamcmd.sh
#   Config: ~/.steam/config/config.vdf
#   Binary: ~/.steam/steamcmd/linux64/steamclient.so


class _SteamCmdFinder:

    def __init__(self):
        self._steamcmd_exe, self._last = 'steamcmd', 0.0
        self._config_file, self._steamclient_file = None, None

    async def initialise(self, cwd: str, home_dir: str, env_paths: str) -> bool:
        paths = '/usr/games:/usr/bin'
        if env_paths:
            paths += ':' + env_paths
        steamcmd_exe = await io.find_in_env_path(paths, 'steamcmd')
        for home in (home_dir, cwd):
            if not steamcmd_exe and await io.file_exists(home + '/steamcmd.sh'):
                steamcmd_exe = home + '/steamcmd.sh'
        self._steamcmd_exe = steamcmd_exe if steamcmd_exe else '~/Steam/steamcmd.sh'
        return bool(steamcmd_exe)

    def script_refresh(self) -> str:
        return self._steamcmd_exe + ' +quit >/dev/null 2>&1'

    def script_execute(self) -> str:
        script, now = self._steamcmd_exe, time.time()
        if now - self._last > 3600.0:  # 1 hour
            script = self.script_refresh() + '\nsleep 1\n' + script
            self._last = now
        return script

    async def config_file(self, home_dir: str) -> str | None:
        if not self._config_file:
            for rpath in ('/.local/share/Steam', '/.steam', '/Steam'):
                apath = home_dir + rpath + '/config/config.vdf'
                if not self._config_file and await io.file_exists(apath):
                    self._config_file = apath
        return self._config_file

    async def steamclient_file(self, home_dir: str) -> str | None:
        if not self._steamclient_file:
            for rpath in ('/.local/share/Steam/steamcmd', '/.steam/steamcmd', '/Steam'):
                apath = home_dir + rpath + '/linux64/steamclient.so'
                if not self._steamclient_file and await io.file_exists(apath):
                    self._steamclient_file = apath
        return self._steamclient_file


_STEAMCMD_FINDER = _SteamCmdFinder()


async def get_config_file(home_dir: str) -> str:
    config_file = await _STEAMCMD_FINDER.config_file(home_dir)
    if not config_file:
        raise Exception('Steam config file not found.')
    return config_file


async def link_steamclient_to_sdk(home_dir: str):
    steamclient_file = await _STEAMCMD_FINDER.steamclient_file(home_dir)
    if not steamclient_file:
        return  # silent fail
    sdk_dir = home_dir + '/.steam/sdk64'
    steamclient_link = sdk_dir + '/steamclient.so'
    if await io.symlink_exists(steamclient_link):
        return  # already done
    await io.create_directories(sdk_dir)
    await io.create_symlink(steamclient_link, steamclient_file)
    logging.info('Symlinked %s to %s', steamclient_link, steamclient_file)


async def ensure_steamcmd(cwd: str, home_dir: str, env_paths: str):
    steamcmd_home = None
    for path in ('/.local/share/Steam/steamcmd', '/.steam/steamcmd', '/Steam'):
        if not steamcmd_home and await io.file_exists(home_dir + path + '/steamcmd.sh'):
            steamcmd_home = path
    if steamcmd_home:
        logging.info('SteamCMD: %s', home_dir + steamcmd_home)
    found_steamcmd_exe = await _STEAMCMD_FINDER.initialise(cwd, home_dir, env_paths)
    if not found_steamcmd_exe:
        logging.warning('SteamCMD executable not found')
    if steamcmd_home or not found_steamcmd_exe:
        return
    logging.info('SteamCMD installing for service user')
    try:
        await shellutil.run_script(_STEAMCMD_FINDER.script_refresh())
        logging.info('SteamCMD install completed')
    except Exception as e:
        logging.warning('SteamCMD install exception: %s', repr(e))


def steamcmd_script() -> str:
    return _STEAMCMD_FINDER.script_execute()
