import asyncio
import logging
import time
import uuid
from core import util, httpsvc, msgext, msgsvc, msgftr

# TODO support single or chunked responses and transforms


class HttpSubscriptionService:
    SUBSCRIBE = 'HttpSubscriptionService.SubscribeRequest'
    SUBSCRIBE_FILTER = msgftr.NameIs(SUBSCRIBE)
    SUBSCRIBE_RESPONSE = 'HttpSubscriptionService.SubscribeResponse'
    UNSUBSCRIBE = 'HttpSubscriptionService.UnsubscribeRequest'
    UNSUBSCRIBE_FILTER = msgftr.NameIs(UNSUBSCRIBE)
    FILTER = msgftr.Or((SUBSCRIBE_FILTER, UNSUBSCRIBE_FILTER))

    @staticmethod
    async def subscribe(mailer, source, msg_filter):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(msgsvc.Message(source, HttpSubscriptionService.SUBSCRIBE, msg_filter))
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
            subscriber = _Subscriber(self.mailer, identity, message.get_data())
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

    def subscribe_handler(self, msg_filter):
        return _SubscribeHandler(self.mailer, msg_filter)


class _Subscriber:

    def __init__(self, mailer, identity, msg_filter):
        self.mailer = mailer
        self.identity = identity
        self.msg_filter = msgftr.Or((_InactivityCheckProducer.FILTER, msg_filter))
        self.poll_timeout = 60.0
        self.inactivity_timeout = 120.0
        self.queue = asyncio.Queue(maxsize=100)
        self.time_last_activity = time.time()

    def accepts(self, message):
        return self.msg_filter.accepts(message)

    def handle(self, message):
        if _InactivityCheckProducer.FILTER.accepts(message):
            now = message.get_created()
            if self.time_last_activity < 0.0 or ((now - self.time_last_activity) < self.inactivity_timeout):
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
            message = await asyncio.wait_for(self.queue.get(), self.poll_timeout)
            self.queue.task_done()
            return message
        except asyncio.exceptions.TimeoutError:
            return None
        finally:
            self.time_last_activity = time.time()


class _SubscriptionsHandler:

    def __init__(self, service):
        self.service = service

    async def handle_get(self, resource, data):
        subscriber = self.service.lookup(util.get('identity', data))
        if subscriber is None:
            return httpsvc.ResponseBody.NOT_FOUND
        message = await subscriber.get()
        if message is None:
            return httpsvc.ResponseBody.NO_CONTENT
        return message.get_data()


class _SubscribeHandler:

    def __init__(self, mailer, msg_filter):
        self.mailer = mailer
        self.msg_filter = msg_filter

    async def handle_post(self, resource, data):
        url = await HttpSubscriptionService.subscribe(self.mailer, self, self.msg_filter)
        return {'url': url}


class _InactivityCheckProducer:
    CHECK_INACTIVITY = 'HttpSubscriber.CheckInactivity'
    FILTER = msgftr.NameIs(CHECK_INACTIVITY)

    async def next_message(self):
        await asyncio.sleep(200)
        return msgsvc.Message(self, _InactivityCheckProducer.CHECK_INACTIVITY)
