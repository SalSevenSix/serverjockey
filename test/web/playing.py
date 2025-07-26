import unittest
import random
import time
import re
from test.web import webcontext
from selenium.webdriver.support.ui import Select
from core.util import util, dtutil
from core.msgc import sc


class TestPlaying(unittest.TestCase):

    def _start_server(self, identity: str, module: str):
        # open instance page
        context = webcontext.get()
        context.goto_instance(identity, module)
        self.assertTrue(context.get_instance_state() in (sc.READY, sc.STOPPED))
        # start server
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state(sc.STARTED, wait=300.0)

    def _start_server_and_wait_for_login(self, identity: str, module: str) -> str:
        context = webcontext.get()
        self._start_server(identity, module)
        # open players, commands, and chat sections
        if context.has_element('collapsibleConsoleCommands'):
            context.find_element('collapsibleConsoleCommands').click()
        context.find_element('collapsiblePlayers').click()
        context.find_element('collapsibleChatLog').click()
        # wait for player to login
        self.assertIsNotNone(context.find_element('playersColumn0', exists=600.0))
        player_name = context.get_cell_text(
            'playersColumn0', 1, 2 if context.has_element('playersHeaderSteamID') else 1)
        time.sleep(5.0)  # grace to allow player to fully load in
        return player_name

    def _wait_for_logout_and_stop_server(self, player_name: str, nochat: bool = False):
        # wait for player to logout
        context = webcontext.get()
        self.assertIsNotNone(context.find_element('playersZeroOnline', exists=600.0))
        time.sleep(3.0)  # grace to allow activity to save
        # query all player activity from last 10 minutes
        Select(context.find_element('queryDateRangeChatLogSfromms')).select_by_value('0')
        context.find_element('queryDateRangeChatLogIfromdt').send_keys(dtutil.format_time_standard(time.time() - 600.0))
        context.find_element('queryChatTypesChatLogBoth').click()
        context.find_element('queryExecuteChatLog').click()
        self.assertIsNotNone(context.find_element('chatActivityChatLogList', exists=3.0))
        # check expected player activity
        row = 2
        self.assertEqual(player_name, context.get_cell_text('chatActivityChatLogList', row, 2))
        self.assertEqual(sc.LOGIN, util.rchop(context.get_cell_text('chatActivityChatLogList', row, 3), '('))
        if not nochat:
            row += 1
            self.assertEqual(player_name, context.get_cell_text('chatActivityChatLogList', row, 2))
            self.assertEqual('hello from game', context.get_cell_text('chatActivityChatLogList', row, 3))
        row += 1
        self.assertEqual(player_name, context.get_cell_text('chatActivityChatLogList', row, 2))
        self.assertEqual(sc.LOGOUT, util.rchop(context.get_cell_text('chatActivityChatLogList', row, 3), '('))
        self._stop_server()

    # noinspection PyMethodMayBeStatic
    def _stop_server(self):
        context = webcontext.get()
        context.scroll_to_top()
        time.sleep(0.5)
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state(sc.STOPPED, wait=20.0)

    def _send_console_command(self, wait: float = 2.0):
        context = webcontext.get()
        context.find_element('commandBuilderSend').click()
        time.sleep(wait / 2)
        notification = context.find_element('notificationsText0')
        self.assertTrue(notification.get_attribute('innerText').find('command sent') > -1)
        notification.click()
        time.sleep(wait / 2)

    def _check_status_info(self, version_regex: str, port: int):
        context = webcontext.get()
        self.assertIsNotNone(re.compile(version_regex).match(
            context.find_element('serverStatusVersion').get_attribute('innerText')))
        self.assertEqual(context.net_public + ':' + str(port),
                         context.find_element('serverStatusConnect').get_attribute('innerText').strip())

    def test_playing_projectzomboid(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('pz', 'projectzomboid')
        self._check_status_info(r'^[0-9]*\.[0-9]*\.[0-9]*$', 16261)
        # send welcome message to player
        context.find_element('commandBuilderCommandWorld').click()
        context.find_element('commandBuilderActionBroadcast').click()
        context.find_element('commandBuilderImessage').send_keys('Welcome to PZ ' + player_name)
        self._send_console_command()
        # grant admin to player
        context.find_element('commandBuilderCommandPlayers').click()
        context.find_element('commandBuilderActionSetAccessLevel').click()
        context.find_element('commandBuilderIplayer').send_keys(player_name)
        context.find_element('commandBuilderRlevelAdmin').click()
        self._send_console_command()
        # teleport player
        context.find_element('commandBuilderActionTeleAt').click()
        context.find_element('commandBuilderIplayer').send_keys(player_name)
        context.find_element('commandBuilderIlocation').send_keys(str(int(8400 + random.random() * 400)) + ',7200,0')
        self._send_console_command(wait=3.0)
        # revoke admin from player
        context.find_element('commandBuilderActionSetAccessLevel').click()
        context.find_element('commandBuilderIplayer').send_keys(player_name)
        context.find_element('commandBuilderRlevelNone').click()
        self._send_console_command()
        # give item to player
        context.find_element('commandBuilderActionGiveItem').click()
        context.find_element('commandBuilderIplayer').send_keys(player_name)
        context.find_element('commandBuilderIitem').send_keys('Axe')
        self._send_console_command()
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_factorio(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('ft', 'factorio')
        self._check_status_info(r'^2\.[0-9]*\.[0-9]*$', 34197)
        # send welcome message to player
        context.find_element('commandBuilderIline').send_keys('Welcome to FT ' + player_name)
        self._send_console_command()
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_unturned(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('ut', 'unturned')
        self._check_status_info(r'^[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*$', 27027)
        # send welcome message to player
        context.find_element('commandBuilderIline').send_keys('Say Welcome to UT ' + player_name)
        self._send_console_command()
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_sevendaystodie(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('7d2d', 'sevendaystodie')
        self._check_status_info(r'^V 2\.[0-9]* \(b[0-9]*\)$', 26900)
        self.assertEqual('8080', context.find_element('serverStatusCport').get_attribute('innerText'))
        # no console feature to send welcome message
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_starbound(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('sb', 'starbound')
        self._check_status_info(r'^1\.[0-9]*\.[0-9]*$', 21025)
        # no console command to send welcome message
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_valheim(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('vh', 'valheim')
        self._check_status_info(r'^0\.[0-9]*\.[0-9]*$', 2456)
        # no console feature to send welcome message
        self._wait_for_logout_and_stop_server(player_name, nochat=True)

    def test_playing_palworld(self):
        context = webcontext.get()
        self._start_server('pw', 'palworld')
        time.sleep(10.0)  # grace to allow server to fully start
        self._check_status_info(r'^v[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*$', 8211)
        # send welcome message
        context.find_element('collapsibleConsoleCommands').click()
        context.find_element('commandBuilderIline').send_keys('Broadcast Welcome_to_PW')
        self._send_console_command()
        time.sleep(2.0)
        self.assertEqual('Broadcasted: Welcome_to_PW', context.get_instance_loglastline())
        self._stop_server()
