from __future__ import annotations
import asyncio
import logging
import time
import uuid
import typing
# ALLOW const.* util.* msg.* context.* http.httpabc
from core.util import aggtrf, util
from core.msg import msgabc, msgext, msgftr, msgtrf
from core.http import httpabc


class Selector:

    @staticmethod
    def from_argv(*argv):
        msg_filter, transformer, aggregator, completed_filter = None, None, None, None
        for arg in argv:
            if isinstance(arg, Selector):
                return arg
            if isinstance(arg, msgabc.Filter):
                if msg_filter is None:
                    msg_filter = arg
                elif completed_filter is None:
                    completed_filter = arg
            if isinstance(arg, msgabc.Transformer):
                transformer = arg
            if isinstance(arg, aggtrf.Aggregator):
                aggregator = arg
        return Selector(msg_filter, transformer, aggregator, completed_filter)

    def __init__(self,
                 msg_filter: typing.Optional[msgabc.Filter] = None,
                 transformer: typing.Optional[msgabc.Transformer] = None,
                 aggregator: typing.Optional[aggtrf.Aggregator] = None,
                 completed_filter: typing.Optional[msgabc.Filter] = None):
        self.msg_filter = msg_filter if msg_filter else msgftr.AcceptAll()
        self.transformer = transformer if transformer else msgtrf.GetData()
        self.aggregator = aggregator
        self.completed_filter = completed_filter if completed_filter else msgftr.AcceptNothing()


class HttpSubscriptionService(msgabc.AbcSubscriber):
    SUBSCRIBE = 'HttpSubscriptionService.SubscribeRequest'
    SUBSCRIBE_RESPONSE = 'HttpSubscriptionService.SubscribeResponse'
    UNSUBSCRIBE = 'HttpSubscriptionService.UnsubscribeRequest'

    @staticmethod
    async def subscribe(mailer: msgabc.MulticastMailer, source: typing.Any, selector: Selector) -> str:
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, HttpSubscriptionService.SUBSCRIBE, selector)
        return response.data()

    @staticmethod
    def unsubscribe(mailer: msgabc.Mailer, source: typing.Any, identity: str):
        mailer.post(source, HttpSubscriptionService.UNSUBSCRIBE, identity)

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.NameIn((HttpSubscriptionService.SUBSCRIBE, HttpSubscriptionService.UNSUBSCRIBE)))
        self._mailer = mailer
        self._subscriptions_path = '/subscriptions'
        self._subscriptions: typing.Dict[str, _Subscriber] = {}
        mailer.register(_InactivityCheck(mailer))
        mailer.register(self)

    def resource(self, resource: httpabc.Resource, name: str) -> str:
        self._subscriptions_path = resource.path() + '/' + name
        return name

    def lookup(self, identity: str) -> _Subscriber | None:
        return util.get(identity, self._subscriptions)

    def handle(self, message):
        name = message.name()
        if name is HttpSubscriptionService.SUBSCRIBE:
            identity = str(uuid.uuid4())
            path = self._subscriptions_path + '/' + identity
            logging.debug('Http subscription created at ' + path)
            subscriber = _Subscriber(self._mailer, identity, message.data())
            self._subscriptions[identity] = subscriber
            self._mailer.register(subscriber)
            self._mailer.post(self, HttpSubscriptionService.SUBSCRIBE_RESPONSE, path, message)
        if name is HttpSubscriptionService.UNSUBSCRIBE:
            if not message.data():
                return None
            identity = str(message.data()).split('/')[-1]
            subscriber = self.lookup(identity)
            if subscriber:
                del self._subscriptions[identity]
                subscriber.close()
        return None

    def subscriptions_handler(self, name: str) -> _SubscriptionsHandler:
        return _SubscriptionsHandler(self, name)

    def handler(self, *argv) -> _SubscribeHandler:
        return _SubscribeHandler(self._mailer, Selector.from_argv(*argv))


class _Subscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer, identity: str, selector: Selector):
        super().__init__(msgftr.Or(_InactivityCheck.FILTER, msgftr.IsStop(),
                                   selector.msg_filter, selector.completed_filter))
        self._mailer, self._identity = mailer, identity
        self._transformer, self._aggregator = selector.transformer, selector.aggregator
        self._collect_filter, self._completed_filter = selector.msg_filter, selector.completed_filter
        self._purge_overflow = selector.aggregator is not None
        self._poll_timeout, self._inactivity_timeout = 60.0, 120.0
        self._queue = asyncio.Queue(maxsize=1000)
        self._running, self._time_last_activity = True, time.time()

    def handle(self, message):
        if not self._running:
            return True
        if _InactivityCheck.FILTER.accepts(message):
            now, last = message.created(), self._time_last_activity
            if last < 0.0 or ((now - last) < self._inactivity_timeout):
                return None
            logging.debug('Http subscription inactive, unsubscribing ' + self._identity)
            HttpSubscriptionService.unsubscribe(self._mailer, self, self._identity)
            return True
        # noinspection PyBroadException
        try:
            if self._purge_overflow and self._queue.full():
                self._queue.get_nowait()
                self._queue.task_done()
            self._queue.put_nowait(message)
            return None
        except Exception:
            logging.debug('Http subscription queue is full, unsubscribing ' + self._identity)
            HttpSubscriptionService.unsubscribe(self._mailer, self, self._identity)
            return True

    def close(self):
        self._running = False
        util.clear_queue(self._queue)

    async def get(self) -> typing.Union[httpabc.ABC_RESPONSE, msgabc.STOP, None]:
        self._time_last_activity = -1.0
        try:
            result = await self._get()
            if result is msgabc.STOP:
                logging.debug('Http subscription completed, unsubscribing ' + self._identity)
                HttpSubscriptionService.unsubscribe(self._mailer, self, self._identity)
            return result
        finally:
            self._time_last_activity = time.time()

    async def _get(self) -> typing.Union[httpabc.ABC_RESPONSE, msgabc.STOP, None]:
        if self._aggregator is None:
            message = await self._get_one()
            if message is None or message is msgabc.STOP:
                return message
            if self._completed_filter.accepts(message):
                if self._collect_filter.accepts(message):
                    self._queue.put_nowait(msgabc.STOP)
                else:
                    return msgabc.STOP
            return self._transformer.transform(message)
        messages = await self._get_all()
        message_count = len(messages)
        if message_count == 0:
            return None
        last_message = messages[-1]
        if last_message is msgabc.STOP:
            return msgabc.STOP
        if self._completed_filter.accepts(last_message):
            if not self._collect_filter.accepts(last_message):
                if message_count == 1:
                    return msgabc.STOP
                messages.remove(last_message)
            self._queue.put_nowait(msgabc.STOP)
        return self._aggregator.aggregate([self._transformer.transform(m) for m in messages])

    async def _get_all(self) -> typing.List[msgabc.Message]:
        messages = []
        if self._queue.empty():
            message = await self._get_one()
            if message is not None:
                messages.append(message)
            return messages
        try:
            while True:
                message = self._queue.get_nowait()
                messages.append(message)
                self._queue.task_done()
                if message is msgabc.STOP or self._completed_filter.accepts(message):
                    return messages
        except asyncio.QueueEmpty:
            pass
        return messages

    async def _get_one(self) -> typing.Union[msgabc.Message, None]:
        try:
            message = await asyncio.wait_for(self._queue.get(), self._poll_timeout)
            self._queue.task_done()
            return message
        except asyncio.TimeoutError:
            return None


class _SubscriptionsHandler(httpabc.GetHandler):

    def __init__(self, service: HttpSubscriptionService, name: str):
        self._service, self._name = service, name

    async def handle_get(self, resource, data):
        identity = util.get(self._name, data)
        subscriber = self._service.lookup(identity)
        if subscriber is None:
            return httpabc.ResponseBody.NOT_FOUND
        result = await subscriber.get()
        if result is msgabc.STOP:
            return httpabc.ResponseBody.NOT_FOUND
        if result is None:
            return httpabc.ResponseBody.NO_CONTENT
        return result


class _SubscribeHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, selector: Selector):
        self._mailer, self._selector = mailer, selector

    async def handle_post(self, resource, data):
        path = await HttpSubscriptionService.subscribe(self._mailer, self, self._selector)
        return {'url': util.get('baseurl', data, '') + path}


class _InactivityCheck(msgabc.AbcSubscriber):
    CHECK_INACTIVITY = 'HttpSubscriber.CheckInactivity'
    FILTER = msgftr.NameIs(CHECK_INACTIVITY)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.AcceptAll())
        self._mailer = mailer
        self._last_check = time.time()

    def handle(self, message):
        now = message.created()
        if (now - self._last_check) > 200.0:
            self._last_check = now
            self._mailer.post(self, _InactivityCheck.CHECK_INACTIVITY)
        return None
