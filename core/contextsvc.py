from core import msgsvc, util


class Context:

    def __init__(self, **kwargs):
        self.parent = None
        self.configuration = kwargs.copy() if kwargs else {}
        self.mailer = msgsvc.MulticastMailer()
        self.mailer.start()

    def create_subcontext(self, **kwargs):
        context = Context(**kwargs)
        context.parent = self
        return context

    def config(self, key):
        value = util.get(key, self.configuration)
        if value is not None or self.parent is None:
            return value
        return self.parent.config(value)

    def is_debug(self):
        return self.config('debug')

    def register(self, subscriber):
        return self.mailer.register(subscriber)

    def post(self, *vargs):
        return self.mailer.post(*vargs)

    async def shutdown(self):
        await self.mailer.stop()
