import abc
# ALLOW const.* util.* msg*.* context.* http.* store.*
from core.const import gc
from core.util import util, objconv
from core.msg import msgabc, msgftr
from core.msgc import mc
from core.context import contextsvc
from core.http import httpabc, httpcnt, httprsc, httpext
from core.store import storeabc, storetxn, storesvc


class SystemStoreService:

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._dbfile = context.config('dbfile')

    def initialise(self):
        if not self._dbfile:
            return
        self._context.register(storesvc.StoreService(self._context))
        self._context.post(self, storesvc.StoreService.INITIALISE)
        self._context.register(_SystemRouting(self._context))

    def initialise_instance(self, subcontext: contextsvc.Context):
        if not self._dbfile:
            return
        subcontext.register(_InstanceRouting(subcontext))

    def resources(self, resource: httprsc.WebResource):
        if not self._dbfile:
            return
        r = httprsc.ResourceBuilder(resource)
        r.psh('store', httpext.StaticHandler(self._dbfile))
        r.put('reset', _StoreResetHandler(self._context))
        r.psh('instance', _QueryInstanceHandler(self._context))
        r.put('event', _QueryInstanceEventHandler(self._context))
        r.pop()
        r.psh('player')
        r.put('event', _QueryPlayerEventHandler(self._context))
        r.put('chat', _QueryPlayerChatHandler(self._context))


class _SystemRouting(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(mc.SystemService.SERVER_FILTER)
        self._mailer = mailer

    async def handle(self, message):
        source, name, subcontext = message.source(), message.name(), message.data()
        identity, module = subcontext.config('identity'), subcontext.config('module')
        if name is mc.SystemService.SERVER_INITIALISED:
            storeabc.execute(self._mailer, source, storetxn.InsertInstance(identity, module))
            return None
        if name is mc.SystemService.SERVER_DELETED:
            storeabc.execute(self._mailer, source, storetxn.DeleteInstance(identity))
            return None
        return None


class _InstanceRouting(msgabc.AbcSubscriber):
    _LOGIN, _LOGOUT, _CLEAR, _CHAT = 'LOGIN', 'LOGOUT', 'CLEAR', 'CHAT'

    def __init__(self, subcontext: contextsvc.Context):
        super().__init__(msgftr.Or(mc.ServerStatus.UPDATED_FILTER, mc.PlayerStore.EVENT_FILTER))
        self._identity, self._mailer = subcontext.config('identity'), subcontext.root()
        self._last_state, self._player_names = gc.READY, set()

    async def handle(self, message):
        source, data = message.source(), message.data()
        if mc.ServerStatus.UPDATED_FILTER.accepts(message):
            state = util.get('state', data)
            if state == self._last_state:
                return None
            self._last_state = state
            details = objconv.obj_to_json(util.get('details', data))
            storeabc.execute(self._mailer, source, storetxn.InsertInstanceEvent(self._identity, state, details))
            return None
        if mc.PlayerStore.EVENT_FILTER.accepts(message):
            event = data.asdict()
            event_name = event['event'].upper()
            if event_name == _InstanceRouting._CLEAR:
                for player_name in self._player_names:
                    storeabc.execute(self._mailer, source, storetxn.InsertPlayerEvent(
                        self._identity, _InstanceRouting._LOGOUT, player_name, None))
                self._player_names = set()
                return None
            player_name = event['player']['name']
            if event_name == _InstanceRouting._CHAT:
                storeabc.execute(self._mailer, source, storetxn.InsertPlayerChat(
                    self._identity, player_name, event['text']))
                return None
            steamid = event['player']['steamid']
            if event_name == _InstanceRouting._LOGIN:
                self._player_names.add(player_name)
                storeabc.execute(self._mailer, source, storetxn.InsertPlayerEvent(
                    self._identity, event_name, player_name, steamid))
                return None
            if event_name == _InstanceRouting._LOGOUT:
                self._player_names.remove(player_name)
                storeabc.execute(self._mailer, source, storetxn.InsertPlayerEvent(
                    self._identity, event_name, player_name, steamid))
                return None
            return None


class _StoreResetHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.Mailer):
        self._mailer = mailer

    def handle_post(self, resource, data):
        self._mailer.post(self, storesvc.StoreService.RESET)
        return httpabc.ResponseBody.NO_CONTENT


class _AbstractQueryHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        result = await storeabc.query(self._mailer, self, self.get_query(data))
        if isinstance(result, Exception):
            return httpabc.ResponseBody.BAD_REQUEST
        return result

    @abc.abstractmethod
    def get_query(self, data) -> storeabc.Transaction:
        pass


class _QueryInstanceHandler(_AbstractQueryHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(mailer)

    def get_query(self, data):
        return storetxn.SelectInstance(data)


class _QueryInstanceEventHandler(_AbstractQueryHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(mailer)

    def get_query(self, data):
        return storetxn.SelectInstanceEvent(data)


class _QueryPlayerEventHandler(_AbstractQueryHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(mailer)

    def get_query(self, data):
        return storetxn.SelectPlayerEvent(data)


class _QueryPlayerChatHandler(_AbstractQueryHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(mailer)

    def get_query(self, data):
        return storetxn.SelectPlayerChat(data)
