import logging
# ALLOW core.* projectzomboid.messaging
from core.util import io
from core.msg import msgabc, msgftr, msgpipe
from core.msgc import mc
from servers.projectzomboid import messaging as msg


class ScraperService(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer, logs_dir: str):
        super().__init__(msgftr.Or(
            msgftr.IsStop(), mc.ServerStatus.RUNNING_FALSE_FILTER,
            msgftr.And(msg.CONSOLE_OUTPUT_FILTER, msgftr.DataStrContains('[fully-connected]'))))
        self._mailer, self._logs_dir = mailer, logs_dir
        self._player_publisher, self._chat_publisher = None, None

    async def handle(self, message):
        if message is msgabc.STOP or mc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            if self._chat_publisher:
                self._chat_publisher.stop()
            if self._player_publisher:
                self._player_publisher.stop()
            self._player_publisher, self._chat_publisher = None, None
            return True if message is msgabc.STOP else None
        if not self._player_publisher:
            player_log = await self._find_latest_log('_user.txt')
            if player_log:
                player_publisher = msgpipe.TailPublisher(self._mailer, self, mc.ServerProcess.STDOUT_LINE, player_log)
                if await player_publisher.start():
                    self._player_publisher = player_publisher
        if not self._chat_publisher:
            chat_log = await self._find_latest_log('_chat.txt')
            if chat_log:
                chat_publisher = msgpipe.TailPublisher(self._mailer, self, mc.ServerProcess.STDOUT_LINE, chat_log)
                if await chat_publisher.start():
                    self._chat_publisher = chat_publisher
        return None

    async def _find_latest_log(self, endswith: str) -> str | None:
        try:
            files = await io.directory_list(self._logs_dir)
            files = [o for o in files if o['type'] == 'file' and o['name'].endswith(endswith)]
            latest = dict(name='', mtime=0.0)
            for current in files:
                if current['mtime'] > latest['mtime']:
                    latest = current
            return self._logs_dir + '/' + latest['name'] if latest['name'] else None
        except Exception as e:
            logging.warning('Error find_player_log(%s) %s', self._logs_dir, repr(e))
        return None
