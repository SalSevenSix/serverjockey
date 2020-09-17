from core import util


class PlayerStore:

    def __init__(self):
        self.data = {}

    def add_player(self, player):
        names = util.get(player.get_steamid(), self.data)
        if names:
            if player.get_name() not in names:
                names.append(player.get_name())
        else:
            self.data.update({player.get_steamid(): [player.get_name()]})

    def find_steamid(self, name):
        for steamid, names in iter(self.data.items()):
            if name in names:
                return steamid
        return None

    def asdict(self):
        return self.data.copy()


class PlayerEvent:

    # TODO timestamp
    def __init__(self, event, player):
        self.event = event
        self.player = player

    def get_player(self):
        return self.player

    def asdict(self):
        return {'event': self.event, 'player': self.player.asdict()}


class Player:

    def __init__(self, steamid, name, url=None):
        self.data = {'url': url, 'steamid': steamid, 'name': name}

    def get_steamid(self):
        return self.data['steamid']

    def get_name(self):
        return self.data['name']

    def asdict(self):
        return self.data.copy()


class Option:

    def __init__(self, option, value, url=None):
        self.data = {'url': url, 'option': option, 'value': value}

    def get_option(self):
        return self.data['option']

    def asdict(self):
        return self.data.copy()
