import asyncio
import logging
import time
import uuid
from core import util, httpsvc, msgext, msgsvc, msgftr, msgtrf, aggtrf


class Selector:

    @staticmethod
    def from_argv(*argv):
        msg_filter, transformer, aggregator = None, None, None
        for arg in iter(argv):
            if isinstance(arg, Selector):
                return arg
            if msgftr.is_filter(arg):
                msg_filter = arg
            if msgtrf.is_transformer(arg):
                transformer = arg
            if aggtrf.is_aggregator(arg):
                aggregator = arg
        return Selector(msg_filter, transformer, aggregator)

    def __init__(self, msg_filter=None, transformer=None, aggregator=None):
        self.msg_filter = msg_filter if msg_filter else msgftr.AcceptAll()
        self.transformer = transformer if transformer else msgtrf.GetData()
        self.aggregator = aggregator


class HttpSubscriptionService:
    SUBSCRIBE = 'HttpSubscriptionService.SubscribeRequest'
    SUBSCRIBE_FILTER = msgftr.NameIs(SUBSCRIBE)
    SUBSCRIBE_RESPONSE = 'HttpSubscriptionService.SubscribeResponse'
    UNSUBSCRIBE = 'HttpSubscriptionService.UnsubscribeRequest'
    UNSUBSCRIBE_FILTER = msgftr.NameIs(UNSUBSCRIBE)
    FILTER = msgftr.Or((SUBSCRIBE_FILTER, UNSUBSCRIBE_FILTER))

    @staticmethod
    async def subscribe(mailer, source, selector):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(msgsvc.Message(source, HttpSubscriptionService.SUBSCRIBE, selector))
        return response.get_data()

    @staticmethod
    def unsubscribe(mailer, source, identity):
        mailer.post((source, HttpSubscriptionService.UNSUBSCRIBE, identity))

    def __init__(self, mailer, subscriptions_url):
        self.mailer = mailer
        self.subscriptions_url = subscriptions_url
        self.subscriptions = {}
        self.publisher = msgext.Publisher(mailer, _InactivityCheckProducer())
        mailer.register(self)

    def lookup(self, identity):
        return util.get(identity, self.subscriptions)

    def accepts(self, message):
        return HttpSubscriptionService.FILTER.accepts(message)

    def handle(self, message):
        if HttpSubscriptionService.SUBSCRIBE_FILTER.accepts(message):
            identity = str(uuid.uuid4())
            url = self.subscriptions_url + '/' + identity
            selector = message.get_data()
            subscriber = _Subscriber(self.mailer, identity, selector)
            self.subscriptions.update({identity: subscriber})
            self.mailer.register(subscriber)
            self.mailer.post((self, HttpSubscriptionService.SUBSCRIBE_RESPONSE, url, message))
        if HttpSubscriptionService.UNSUBSCRIBE_FILTER.accepts(message):
            identity = message.get_data()
            if self.lookup(identity):
                self.subscriptions.pop(identity)
        return None

    def subscriptions_handler(self):
        return _SubscriptionsHandler(self)

    def handler(self, *argv):
        return _SubscribeHandler(self.mailer, Selector.from_argv(*argv))


class _Subscriber:

    def __init__(self, mailer, identity, selector):
        self.mailer = mailer
        self.identity = identity
        self.transformer = selector.transformer
        self.aggregator = selector.aggregator
        self.msg_filter = msgftr.Or((_InactivityCheckProducer.FILTER, selector.msg_filter))
        self.poll_timeout = 60.0
        self.inactivity_timeout = 120.0
        self.queue = asyncio.Queue(maxsize=200)
        self.time_last_activity = time.time()

    def accepts(self, message):
        return self.msg_filter.accepts(message)

    def handle(self, message):
        if _InactivityCheckProducer.FILTER.accepts(message):
            now = message.get_created()
            last = self.time_last_activity
            if last < 0.0 or ((now - last) < self.inactivity_timeout):
                return None
            HttpSubscriptionService.unsubscribe(self.mailer, self, self.identity)
            return True
        try:
            self.queue.put_nowait(message)
            return None
        except Exception as e:
            logging.info('Http subscription queue is full, unsubscribing ' + self.identity)
            HttpSubscriptionService.unsubscribe(self.mailer, self, self.identity)
            return True

    async def get(self):
        self.time_last_activity = -1.0
        try:
            if not self.aggregator:
                return await self._get_wait()
            results = self._get_all()
            if len(results) == 0:
                result = await self._get_wait()
                if result is None:
                    return None
                results.append(result)
            return self.aggregator.aggregate(results)
        finally:
            self.time_last_activity = time.time()

    async def _get_wait(self):
        try:
            message = await asyncio.wait_for(self.queue.get(), self.poll_timeout)
            self.queue.task_done()
            return self.transformer.transform(message)
        except asyncio.TimeoutError:
            return None

    def _get_all(self):
        results = []
        if self.queue.qsize() == 0:
            return results
        try:
            while True:
                message = self.queue.get_nowait()
                results.append(self.transformer.transform(message))
                self.queue.task_done()
        except asyncio.QueueEmpty:
            pass
        return results


class _SubscriptionsHandler:

    def __init__(self, service):
        self.service = service

    async def handle_get(self, resource, data):
        subscriber = self.service.lookup(util.get('identity', data))
        if subscriber is None:
            return httpsvc.ResponseBody.NOT_FOUND
        result = await subscriber.get()
        if result is None:
            return httpsvc.ResponseBody.NO_CONTENT
        return result


class _SubscribeHandler:

    def __init__(self, mailer, selector):
        self.mailer = mailer
        self.selector = selector

    async def handle_post(self, resource, data):
        url = await HttpSubscriptionService.subscribe(self.mailer, self, self.selector)
        return {'url': url}


class _InactivityCheckProducer:
    CHECK_INACTIVITY = 'HttpSubscriber.CheckInactivity'
    FILTER = msgftr.NameIs(CHECK_INACTIVITY)

    async def next_message(self):
        await asyncio.sleep(200)
        return msgsvc.Message(self, _InactivityCheckProducer.CHECK_INACTIVITY)
