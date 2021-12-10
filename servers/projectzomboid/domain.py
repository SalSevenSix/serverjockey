import typing
from core.util import util
from core.msg import msgabc, msgext, msgftr
from core.http import httpabc
from core.proc import proch
from servers.projectzomboid import playerstore as pls


class Option:

    def __init__(self, option: str, value: str, url: typing.Optional[str] = None):
        self._data = {'url': url, 'option': option, 'value': value}

    def option(self) -> str:
        return self._data['option']

    def asdict(self) -> dict:
        return self._data.copy()


class OptionLoader:

    def __init__(self,
                 mailer: msgabc.MulticastMailer,
                 source: typing.Any,
                 resource: typing.Optional[httpabc.Resource] = None):
        self._mailer = mailer
        self._source = source
        self._resource = resource

    async def all(self) -> typing.Collection[Option]:
        response = await proch.PipeInLineService.request(
            self._mailer, self._source, 'showoptions', msgext.MultiCatcher(
                catch_filter=proch.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataEquals('List of Server Options:'), include_start=False,
                stop_filter=msgftr.DataStrContains('ServerWelcomeMessage'), include_stop=True))
        options = []
        if not response:
            return options
        for line in iter([m.data() for m in response]):
            if line.startswith('* '):
                option, value = line[2:].split('=')
                url = self._resource.path({'option': option}) if self._resource else None
                options.append(Option(option, value, url))
        return options

    async def get(self, option: str) -> typing.Optional[Option]:
        if option is None:
            return None
        options = [o for o in await self.all() if o.option() == option]
        return util.single(options)


class Player:

    def __init__(self, steamid: str, name: str, url: typing.Optional[str] = None):
        self._data = {'url': url, 'steamid': steamid, 'name': name}

    def steamid(self) -> str:
        return self._data['steamid']

    def name(self) -> str:
        return self._data['name']

    def asdict(self) -> dict:
        return self._data.copy()


class PlayerLoader:

    def __init__(self,
                 mailer: msgabc.MulticastMailer,
                 source: typing.Any,
                 resource: typing.Optional[httpabc.Resource] = None):
        self._mailer = mailer
        self._source = source
        self._resource = resource

    async def all(self) -> typing.Collection[Player]:
        response = await proch.PipeInLineService.request(
            self._mailer, self._source, 'players', msgext.MultiCatcher(
                catch_filter=proch.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataMatches('.*> Players connected.*'), include_start=False,
                stop_filter=msgftr.DataEquals(''), include_stop=False))
        players = []
        if not response:
            return players
        playerstore = await pls.PlayerStoreService.get(self._mailer, self._source)
        for line in iter([m.data() for m in response]):
            if line.startswith('-'):
                name = line[1:]
                steamid = playerstore.find_steamid(name)
                url = self._resource.path({'player': name}) if self._resource else None
                players.append(Player(steamid, name, url))
        return players

    async def get(self, name: str) -> typing.Optional[Player]:
        if name is None:
            return None
        players = [o for o in await self.all() if o.name() == name]
        return util.single(players)
