from core.util import cmdutil
from core.msg import msgabc
from core.http import httpabc, httprsc
from core.proc import prcext


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    httprsc.ResourceBuilder(resource) \
        .push('console') \
        .append('{command}', _ConsoleCommandHandler(mailer))


class _ConsoleCommandHandler(httpabc.AsyncPostHandler):
    COMMANDS = cmdutil.CommandLines({'send': '{line}'})

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._handler = prcext.PipeInLineNoContentPostHandler(mailer, self, _ConsoleCommandHandler.COMMANDS)

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)
