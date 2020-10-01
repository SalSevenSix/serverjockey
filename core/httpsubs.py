from __future__ import annotations
import asyncio
import logging
import time
import uuid
import typing
from core import util, httpabc, msgabc, msgext, msgftr, msgtrf, aggtrf


class _Selector:

    @staticmethod
    def from_argv(*argv):
        msg_filter, transformer, aggregator = None, None, None
        for arg in iter(argv):
            if isinstance(arg, _Selector):
                return arg
            if isinstance(arg, msgabc.Filter):
                msg_filter = arg
            if isinstance(arg, msgabc.Transformer):
                transformer = arg
            if isinstance(arg, aggtrf.Aggregator):
                aggregator = arg
        return _Selector(msg_filter, transformer, aggregator)

    def __init__(self,
                 msg_filter: typing.Optional[msgabc.Filter] = None,
                 transformer: typing.Optional[msgabc.Transformer] = None,
                 aggregator: typing.Optional[aggtrf.Aggregator] = None):
        self.msg_filter = msg_filter if msg_filter else msgftr.AcceptAll()
        self.transformer = transformer if transformer else msgtrf.GetData()
        self.aggregator = aggregator


class HttpSubscriptionService(msgabc.Subscriber):
    SUBSCRIBE = 'HttpSubscriptionService.SubscribeRequest'
    SUBSCRIBE_FILTER = msgftr.NameIs(SUBSCRIBE)
    SUBSCRIBE_RESPONSE = 'HttpSubscriptionService.SubscribeResponse'
    UNSUBSCRIBE = 'HttpSubscriptionService.UnsubscribeRequest'
    UNSUBSCRIBE_FILTER = msgftr.NameIs(UNSUBSCRIBE)
    FILTER = msgftr.Or(SUBSCRIBE_FILTER, UNSUBSCRIBE_FILTER)

    @staticmethod
    async def subscribe(mailer: msgabc.MulticastMailer, source: typing.Any, selector: _Selector) -> str:
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, HttpSubscriptionService.SUBSCRIBE, selector)
        return response.data()

    @staticmethod
    def unsubscribe(mailer: msgabc.Mailer, source: typing.Any, identity: str):
        mailer.post(source, HttpSubscriptionService.UNSUBSCRIBE, identity)

    def __init__(self, mailer: msgabc.MulticastMailer, subscriptions_url: str):
        self._mailer = mailer
        self._subscriptions_url = subscriptions_url
        self._subscriptions: typing.Dict[str, _Subscriber] = {}
        mailer.register(_InactivityCheck(mailer))
        mailer.register(self)

    def lookup(self, identity: str) -> _Subscriber:
        return util.get(identity, self._subscriptions)

    def accepts(self, message):
        return HttpSubscriptionService.FILTER.accepts(message)

    def handle(self, message):
        if HttpSubscriptionService.SUBSCRIBE_FILTER.accepts(message):
            identity = str(uuid.uuid4())
            url = self._subscriptions_url + '/' + identity
            selector = message.data()
            subscriber = _Subscriber(self._mailer, identity, selector)
            self._subscriptions.update({identity: subscriber})
            self._mailer.register(subscriber)
            self._mailer.post(self, HttpSubscriptionService.SUBSCRIBE_RESPONSE, url, message)
        if HttpSubscriptionService.UNSUBSCRIBE_FILTER.accepts(message):
            identity = message.data()
            if self.lookup(identity):
                self._subscriptions.pop(identity)
        return None

    def subscriptions_handler(self) -> _SubscriptionsHandler:
        return _SubscriptionsHandler(self)

    def handler(self, *argv) -> _SubscribeHandler:
        return _SubscribeHandler(self._mailer, _Selector.from_argv(*argv))


class _Subscriber(msgabc.Subscriber):

    def __init__(self, mailer: msgabc.MulticastMailer, identity: str, selector: _Selector):
        self._mailer = mailer
        self._identity = identity
        self._transformer = selector.transformer
        self._aggregator = selector.aggregator
        self._msg_filter = msgftr.Or(_InactivityCheck.FILTER, selector.msg_filter)
        self._poll_timeout = 60.0
        self._inactivity_timeout = 120.0
        self._queue = asyncio.Queue(maxsize=200)
        self._time_last_activity = time.time()

    def accepts(self, message):
        return self._msg_filter.accepts(message) or message is msgabc.STOP

    def handle(self, message):
        if _InactivityCheck.FILTER.accepts(message):
            now = message.created()
            last = self._time_last_activity
            if last < 0.0 or ((now - last) < self._inactivity_timeout):
                return None
            logging.info('Http subscription inactive, unsubscribing ' + self._identity)
            HttpSubscriptionService.unsubscribe(self._mailer, self, self._identity)
            return True
        try:
            self._queue.put_nowait(message)
            return None
        except Exception:
            logging.info('Http subscription queue is full, unsubscribing ' + self._identity)
            HttpSubscriptionService.unsubscribe(self._mailer, self, self._identity)
            return True

    async def get(self) -> typing.Union[httpabc.ABC_RESPONSE, msgabc.STOP, None]:
        self._time_last_activity = -1.0
        try:
            if not self._aggregator:
                return await self._get_wait()
            results = self._get_all()
            if len(results) == 0:
                result = await self._get_wait()
                if result is None:
                    return None
                results.append(result)
            if results[-1] is msgabc.STOP:
                return msgabc.STOP
            return self._aggregator.aggregate(results)
        finally:
            self._time_last_activity = time.time()

    async def _get_wait(self) -> typing.Union[httpabc.ABC_RESPONSE, msgabc.STOP, None]:
        try:
            message = await asyncio.wait_for(self._queue.get(), self._poll_timeout)
            result = message if message is msgabc.STOP else self._transformer.transform(message)
            self._queue.task_done()
            return result
        except asyncio.TimeoutError:
            return None

    def _get_all(self) -> typing.Union[httpabc.ABC_RESPONSE, msgabc.STOP, None]:
        results = []
        if self._queue.qsize() == 0:
            return results
        try:
            while True:
                message = self._queue.get_nowait()
                results.append(message if message is msgabc.STOP else self._transformer.transform(message))
                self._queue.task_done()
                if message is msgabc.STOP:
                    return results
        except asyncio.QueueEmpty:
            pass
        return results


class _SubscriptionsHandler(httpabc.AsyncGetHandler):

    def __init__(self, service: HttpSubscriptionService):
        self._service = service

    async def handle_get(self, resource, data):
        subscriber = self._service.lookup(util.get('identity', data))
        if subscriber is None:
            return httpabc.ResponseBody.NOT_FOUND
        result = await subscriber.get()
        if result is msgabc.STOP:
            return httpabc.ResponseBody.NOT_FOUND
        if result is None:
            return httpabc.ResponseBody.NO_CONTENT
        return result


class _SubscribeHandler(httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, selector: _Selector):
        self._mailer = mailer
        self._selector = selector

    async def handle_post(self, resource, data):
        url = await HttpSubscriptionService.subscribe(self._mailer, self, self._selector)
        return {'url': url}


class _InactivityCheck(msgabc.Subscriber):
    CHECK_INACTIVITY = 'HttpSubscriber.CheckInactivity'
    FILTER = msgftr.NameIs(CHECK_INACTIVITY)

    def __init__(self, mailer: msgabc.Mailer):
        self._mailer = mailer
        self._last_check = time.time()

    def accepts(self, message):
        return True

    def handle(self, message):
        now = message.created()
        if (now - self._last_check) > 200.0:
            self._last_check = now
            self._mailer.post(self, _InactivityCheck.CHECK_INACTIVITY)
        return None
