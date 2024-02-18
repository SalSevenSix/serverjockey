# ALLOW core.* palworld.messaging
from core.msg import msgabc
from core.http import httpabc, httprsc, httpext
from core.common import interceptors, rconsvc


def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(rconsvc.RconService(mailer, enforce_id=False))


def resources(mailer: msgabc.MulticastMailer, resource: httpabc.Resource):
    r = httprsc.ResourceBuilder(resource)
    r.reg('s', interceptors.block_not_started(mailer))
    r.psh('console')
    r.put('help', httpext.StaticHandler(HELP_TEXT))
    r.put('send', rconsvc.RconHandler(mailer), 's')


HELP_TEXT = '''PALWORLD CONSOLE HELP
todo
'''
