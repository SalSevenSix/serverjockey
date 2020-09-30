import typing
from core import httpabc, httpsvc, proch, msgext, util, msgftr, msgabc
from servers.projectzomboid import subscribers as subs, domain as dom


class OptionLoader:
    DECODER = httpabc.DictionaryCoder().append('option', util.b10str_to_str)

    def __init__(self, mailer: msgabc.MulticastMailer, source: typing.Any, resource: httpabc.Resource):
        self._mailer = mailer
        self._source = source
        self._resource = resource

    async def all(self) -> typing.Collection[dom.Option]:
        response = await proch.PipeInLineService.request(
            self._mailer, self._source, 'showoptions', msgext.MultiCatcher(
                catch_filter=proch.Filter.STDOUT_LINE,
                start_filter=msgftr.DataEquals('List of Server Options:'), include_start=False,
                stop_filter=msgftr.DataStrContains('ServerWelcomeMessage'), include_stop=True))
        options = []
        if not response:
            return options
        for line in iter([m.get_data() for m in response]):
            if line.startswith('* '):
                option, value = line[2:].split('=')
                url = httpsvc.PathBuilder(self._resource, 'option') \
                    .append('option', util.str_to_b10str(option)) \
                    .build()
                options.append(dom.Option(option, value, url))
        return options

    async def get(self, option: str) -> typing.Optional[dom.Option]:
        if option is None:
            return None
        options = [o for o in await self.all() if o.get_option() == option]
        return util.single(options)


class PlayerLoader:
    DECODER = httpabc.DictionaryCoder().append('player', util.b10str_to_str)

    def __init__(self, mailer: msgabc.MulticastMailer, source: typing.Any, resource: httpabc.Resource):
        self._mailer = mailer
        self._source = source
        self._resource = resource

    async def all(self) -> typing.Collection[dom.Player]:
        response = await proch.PipeInLineService.request(
            self._mailer, self._source, 'players', msgext.MultiCatcher(
                catch_filter=proch.Filter.STDOUT_LINE,
                start_filter=msgftr.DataMatches('Players connected.*'), include_start=False,
                stop_filter=msgftr.DataEquals(''), include_stop=False))
        players = []
        if not response:
            return players
        playerstore = await subs.CaptureSteamidSubscriber.get_playerstore(self._mailer, self._source)
        for line in iter([m.get_data() for m in response]):
            if line.startswith('-'):
                name = line[1:]
                steamid = playerstore.find_steamid(name)
                url = httpsvc.PathBuilder(self._resource, 'player') \
                    .append('player', util.str_to_b10str(name)) \
                    .build()
                players.append(dom.Player(steamid, name, url))
        return players

    async def get(self, name: str) -> typing.Optional[dom.Player]:
        if name is None:
            return None
        players = [o for o in await self.all() if o.get_name() == name]
        return util.single(players)
