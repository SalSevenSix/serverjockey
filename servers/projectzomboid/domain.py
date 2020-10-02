import typing
from core.util import util


class Option:

    def __init__(self, option: str, value: str, url: typing.Optional[str] = None):
        self._data = {'url': url, 'option': option, 'value': value}

    def option(self) -> str:
        return self._data['option']

    def asdict(self) -> dict:
        return self._data.copy()


class Player:

    def __init__(self, steamid: str, name: str, url: typing.Optional[str] = None):
        self._data = {'url': url, 'steamid': steamid, 'name': name}

    def steamid(self) -> str:
        return self._data['steamid']

    def name(self) -> str:
        return self._data['name']

    def asdict(self) -> dict:
        return self._data.copy()


class PlayerStore:

    def __init__(self):
        self._data: typing.Dict[str, typing.List[str]] = {}

    def add_player(self, player: Player):
        names = util.get(player.steamid(), self._data)
        if names:
            if player.name() not in names:
                names.append(player.name())
        else:
            self._data.update({player.steamid(): [player.name()]})

    def find_steamid(self, name: str) -> typing.Optional[str]:
        for steamid, names in iter(self._data.items()):
            if name in names:
                return steamid
        return None

    def asdict(self) -> dict:
        return self._data.copy()


class PlayerEvent:

    def __init__(self, event: str, player: Player):
        self._created = util.now_millis()
        self._event = event
        self._player = player

    def player(self) -> Player:
        return self._player

    def asdict(self) -> dict:
        return {'created': self._created, 'event': self._event, 'player': self._player.asdict()}
