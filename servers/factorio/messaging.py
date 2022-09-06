from core.util import util
from core.msg import msgabc, msgftr
from core.proc import proch, prcext
from core.system import svrsvc

SERVER_STARTED_FILTER = msgftr.And(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    msgftr.DataMatches(
        '.*Info CommandLineMultiplayer.*Maximum segment size.*maximum-segment-size.*minimum-segment-size.*'))
DEPLOYMENT_MSG = 'Deployment.Message'
CONSOLE_FILTER = msgftr.Or(
    proch.ServerProcess.FILTER_STDOUT_LINE,
    proch.ServerProcess.FILTER_STDERR_LINE,
    proch.JobProcess.FILTER_STDOUT_LINE,
    msgftr.NameIs(DEPLOYMENT_MSG))


class Messaging:

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def initialise(self):
        self._mailer.register(prcext.ServerStateSubscriber(self._mailer))
        self._mailer.register(_ServerDetailsSubscriber(self._mailer))
        self._mailer.register(_PlayerEventSubscriber(self._mailer))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_FILTER = msgftr.DataMatches('.*; Factorio .*build .* headless.*')
    PRIVATE_IP_PORT = msgftr.DataStrContains('Hosting game at IP ADDR:')
    PUBLIC_IP_PORT = msgftr.DataMatches('.*Info.*Own address is IP ADDR.*confirmed by pingpong.*')

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PRIVATE_IP_PORT,
                _ServerDetailsSubscriber.PUBLIC_IP_PORT)))
        self._mailer = mailer

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), 'Factorio')
            value = util.right_chop_and_strip(value, '(build')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'version': value})
            return None
        if _ServerDetailsSubscriber.PRIVATE_IP_PORT.accepts(message) \
                or _ServerDetailsSubscriber.PUBLIC_IP_PORT.accepts(message):
            value = util.left_chop_and_strip(message.data(), '({')
            value = util.right_chop_and_strip(value, '})')
            value = value.split(':')
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'ip': value[0], 'port': value[1]})
            return None
        return None


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    JOIN = '[JOIN]'
    JOIN_FILTER = msgftr.DataStrContains(JOIN)
    LEAVE = '[LEAVE]'
    LEAVE_FILTER = msgftr.DataStrContains(LEAVE)
    PLAYER_EVENT = '_PlayerEventSubscriber.Event'

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.JOIN_FILTER, _PlayerEventSubscriber.LEAVE_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.JOIN)
            value = util.right_chop_and_strip(value, 'joined the game')
            self._mailer.post(
                self, _PlayerEventSubscriber.PLAYER_EVENT,
                {'event': 'login', 'player': {'steamid': False, 'name': value}})
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.LEAVE)
            value = util.right_chop_and_strip(value, 'left the game')
            self._mailer.post(
                self, _PlayerEventSubscriber.PLAYER_EVENT,
                {'event': 'logout', 'player': {'steamid': False, 'name': value}})
            return None
        return None


PLAYER_EVENT_FILTER = msgftr.NameIs(_PlayerEventSubscriber.PLAYER_EVENT)
