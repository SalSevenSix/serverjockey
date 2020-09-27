from core import msgsvc, util


class Context:

    def __init__(self, **configuration):
        self.parent = None
        self.children = []
        self.configuration = configuration.copy() if configuration else {}
        self.mailer = msgsvc.MulticastMailer()

    def start(self):
        return self.mailer.start()

    def create_subcontext(self, **configuration):
        subcontext = Context(**configuration)
        subcontext.parent = self
        self.children.append(subcontext)
        return subcontext

    async def destroy_subcontext(self, subcontext):
        await subcontext.shutdown()
        self.children.remove(subcontext)

    def subcontexts(self):
        return self.children.copy()

    def config(self, key):
        value = util.get(key, self.configuration)
        if value is not None or self.parent is None:
            return value
        return self.parent.config(key)

    def is_debug(self):
        return self.config('debug')

    def register(self, subscriber):
        return self.mailer.register(subscriber)

    def post(self, *vargs):
        return self.mailer.post(*vargs)

    async def shutdown(self):
        for subcontext in iter(self.subcontexts()):
            await self.destroy_subcontext(subcontext)
        await util.silently_cleanup(self.mailer)
