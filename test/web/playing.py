import unittest
import time
from core.util import util, dtutil
from test.web import webcontext
from selenium.webdriver.support.ui import Select


class TestPlaying(unittest.TestCase):

    def _start_server_and_wait_for_login(self, identity: str, module: str) -> str:
        # open instance page
        context = webcontext.get()
        context.goto_instance(identity, module)
        self.assertTrue(context.get_instance_state() in ('READY', 'STOPPED'))
        # start server
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state('STARTED', wait=200.0)
        # open players, commands, and chat sections
        context.find_element('collapsibleConsoleCommands').click()
        context.find_element('collapsibleChatLog').click()
        context.find_element('collapsiblePlayers').click()
        # wait for player to login
        self.assertIsNotNone(context.find_element('playersColumn0', exists=600.0))
        player_name = context.get_cell_text(
            'playersColumn0', 1, 2 if context.has_element('playersHeaderSteamID') else 1)
        time.sleep(5.0)  # grace to allow player to fully load in
        return player_name

    def _wait_for_logout_and_stop_server(self, player_name: str):
        # wait for player to logout
        context = webcontext.get()
        self.assertIsNotNone(context.find_element('playersZeroOnline', exists=600.0))
        time.sleep(2.0)  # grace to allow activity to save
        # query all player activity from last 10 minutes
        Select(context.find_element('queryDateRangeChatLogSfromms')).select_by_value('0')
        context.find_element('queryDateRangeChatLogIfromdt').send_keys(dtutil.format_time_standard(time.time() - 600.0))
        context.find_element('queryChatTypesChatLogBoth').click()
        context.find_element('queryExecuteChatLog').click()
        self.assertIsNotNone(context.find_element('chatActivityChatLogList', exists=3.0))
        # check expected player activity
        self.assertEqual(player_name, context.get_cell_text('chatActivityChatLogList', 2, 2))
        self.assertEqual('LOGIN', util.rchop(context.get_cell_text('chatActivityChatLogList', 2, 3), '('))
        self.assertEqual(player_name, context.get_cell_text('chatActivityChatLogList', 3, 2))
        self.assertEqual('hello from game', context.get_cell_text('chatActivityChatLogList', 3, 3))
        self.assertEqual(player_name, context.get_cell_text('chatActivityChatLogList', 4, 2))
        self.assertEqual('LOGOUT', util.rchop(context.get_cell_text('chatActivityChatLogList', 4, 3), '('))
        # stop server
        context.scroll_to_top()
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state('STOPPED', wait=20.0)

    def test_playing_projectzomboid(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('pz', 'projectzomboid')
        # broadcast message to all players
        context.find_element('commandBuilderCommandWorld').click()
        context.find_element('commandBuilderActionBroadcast').click()
        context.find_element('commandBuilderImessage').send_keys('Welcome ' + player_name)
        context.find_element('commandBuilderSend').click()
        self._wait_for_logout_and_stop_server(player_name)
