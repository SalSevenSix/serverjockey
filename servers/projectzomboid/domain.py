from core import util, proch, msgext, msgftr, httpsvc
from servers.projectzomboid import subscribers as s


class Player:
    DECODER = util.DictionaryCoder().append('player', util.b10str_to_str)

    class Loader:
        def __init__(self, mailer, source, resource):
            self.mailer = mailer
            self.source = source
            self.resource = resource

        async def all(self):
            response = await proch.PipeInLineService.request(
                self.mailer, self.source, 'players', msgext.MultiCatcher(
                    catch_filter=proch.Filter.STDOUT_LINE,
                    start_filter=msgftr.DataMatches('Players connected.*'), include_start=False,
                    stop_filter=msgftr.DataEquals(''), include_stop=False))
            players = []
            if not response.get_data():
                return players
            steamids = await s.CaptureSteamidSubscriber.request(self.mailer, self.source)
            for line in iter([m.get_data() for m in response.get_data()]):
                if line.startswith('-'):
                    name = line[1:]
                    steamid = None
                    for candidate, names in iter(steamids.items()):
                        if name in names:
                            steamid = candidate
                    players.append(Player(self.resource, steamid, name))
            return players

        async def get(self, name=None):
            if name is None:
                return None
            players = [p for p in await self.all() if p.data['name'] == name]
            return None if len(players) == 0 else players[0]

    def __init__(self, resource, steamid, name):
        url = httpsvc.PathBuilder(resource, 'player') \
            .append('player', util.str_to_b10str(name)) \
            .build()
        self.data = {'url': url, 'steamid': steamid, 'name': name}

    def get_data(self):
        return self.data


class Option:
    DECODER = util.DictionaryCoder().append('option', util.b10str_to_str)

    class Loader:
        def __init__(self, mailer, source, resource):
            self.mailer = mailer
            self.source = source
            self.resource = resource

        async def all(self):
            response = await proch.PipeInLineService.request(
                self.mailer, self.source, 'showoptions', msgext.MultiCatcher(
                    catch_filter=proch.Filter.STDOUT_LINE,
                    start_filter=msgftr.DataEquals('List of Server Options:'), include_start=False,
                    stop_filter=msgftr.DataStrContains('ServerWelcomeMessage'), include_stop=True))
            options = []
            if not response.get_data():
                return options
            for line in iter([m.get_data() for m in response.get_data()]):
                if line.startswith('* '):
                    options.append(Option(self.resource, line[2:]))
            return options

        async def get(self, option=None):
            if option is None:
                return None
            options = [p for p in await self.all() if p.data['option'] == option]
            return None if len(options) == 0 else options[0]

    def __init__(self, resource, option_and_value):
        option, value = option_and_value.split('=')
        url = httpsvc.PathBuilder(resource, 'option') \
            .append('option', util.str_to_b10str(option)) \
            .build()
        self.data = {'url': url, 'option': option, 'value': value}

    def get_data(self):
        return self.data
