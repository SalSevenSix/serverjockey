from core import httpsvc, httpext, proch, msgext, util, msgftr
from servers.projectzomboid import subscribers as s, domain as d


class OptionLoader:
    DECODER = httpext.DictionaryCoder().append('option', util.b10str_to_str)

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
                option, value = line[2:].split('=')
                url = httpsvc.PathBuilder(self.resource, 'option') \
                    .append('option', util.str_to_b10str(option)) \
                    .build()
                options.append(d.Option(option, value, url))
        return options

    async def get(self, option):
        if option is None:
            return None
        options = [o for o in await self.all() if o.get_option() == option]
        return None if len(options) == 0 else options[0]


class PlayerLoader:
    DECODER = httpext.DictionaryCoder().append('player', util.b10str_to_str)

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
        playerstore = await s.CaptureSteamidSubscriber.get_playerstore(self.mailer, self.source)
        for line in iter([m.get_data() for m in response.get_data()]):
            if line.startswith('-'):
                name = line[1:]
                steamid = playerstore.find_steamid(name)
                url = httpsvc.PathBuilder(self.resource, 'player') \
                    .append('player', util.str_to_b10str(name)) \
                    .build()
                players.append(d.Player(steamid, name, url))
        return players

    async def get(self, name):
        if name is None:
            return None
        players = [o for o in await self.all() if o.get_name() == name]
        return None if len(players) == 0 else players[0]
