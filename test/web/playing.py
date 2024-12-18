import unittest
import random
import time
import re
from core.util import util, dtutil
from test.web import webcontext
from selenium.webdriver.support.ui import Select


class TestPlaying(unittest.TestCase):

    def _start_server(self, identity: str, module: str):
        # open instance page
        context = webcontext.get()
        context.goto_instance(identity, module)
        self.assertTrue(context.get_instance_state() in ('READY', 'STOPPED'))
        # start server
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state('STARTED', wait=200.0)

    def _start_server_and_wait_for_login(self, identity: str, module: str) -> str:
        context = webcontext.get()
        self._start_server(identity, module)
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
        time.sleep(3.0)  # grace to allow activity to save
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
        self._stop_server()

    # noinspection PyMethodMayBeStatic
    def _stop_server(self):
        context = webcontext.get()
        context.scroll_to_top()
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state('STOPPED', wait=20.0)

    def _send_console_command(self, wait: float = 2.0):
        context = webcontext.get()
        context.find_element('commandBuilderSend').click()
        time.sleep(wait / 2)
        notification = context.find_element('notificationsText0')
        self.assertTrue(notification.get_attribute('innerText').find('command sent') > -1)
        notification.click()
        time.sleep(wait / 2)

    def test_playing_projectzomboid(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('pz', 'projectzomboid')
        # check status info
        self.assertIsNotNone(re.compile(r'^[0-9]*\.[0-9]*\.[0-9]*$').match(
            context.find_element('serverStatusVersion').get_attribute('innerText')))
        self.assertEqual(context.net_public + ':16261',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
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
        context.find_element('commandBuilderImodule').send_keys('Base')
        context.find_element('commandBuilderIitem').send_keys('Axe')
        self._send_console_command()
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_factorio(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('ft', 'factorio')
        # check status info
        self.assertIsNotNone(re.compile(r'^2\.[0-9]*\.[0-9]*$').match(
            context.find_element('serverStatusVersion').get_attribute('innerText')))
        self.assertEqual(context.net_public + ':34197',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
        # send welcome message to player
        context.find_element('commandBuilderIline').send_keys('Welcome to FT ' + player_name)
        self._send_console_command()
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_unturned(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('ut', 'unturned')
        # check status info
        self.assertIsNotNone(re.compile(r'^[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*$').match(
            context.find_element('serverStatusVersion').get_attribute('innerText')))
        self.assertEqual(context.net_public + ':27027',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
        # send welcome message to player
        context.find_element('commandBuilderIline').send_keys('Say Welcome to UT ' + player_name)
        self._send_console_command()
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_sevendaystodie(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('7d2d', 'sevendaystodie')
        # check status info
        self.assertIsNotNone(re.compile(r'^V 1\.[0-9]* \(b[0-9]*\)$').match(
            context.find_element('serverStatusVersion').get_attribute('innerText')))
        self.assertEqual(context.net_public + ':26900',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
        self.assertEqual('8080', context.find_element('serverStatusCport').get_attribute('innerText'))
        # no console feature to send welcome message
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_starbound(self):
        context, player_name = webcontext.get(), self._start_server_and_wait_for_login('sb', 'starbound')
        # check status info
        self.assertIsNotNone(re.compile(r'^1\.[0-9]*\.[0-9]*$').match(
            context.find_element('serverStatusVersion').get_attribute('innerText')))
        self.assertEqual(context.net_public + ':21025',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
        # no console command to send welcome message
        self._wait_for_logout_and_stop_server(player_name)

    def test_playing_palworld(self):
        context = webcontext.get()
        self._start_server('pw', 'palworld')
        # check status info
        time.sleep(6.0)  # grace to allow server to fully start
        self.assertIsNotNone(re.compile(r'^v[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*$').match(
            context.find_element('serverStatusVersion').get_attribute('innerText')))
        self.assertEqual(context.net_public + ':8211',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
        # send welcome message
        context.find_element('collapsibleConsoleCommands').click()
        context.find_element('commandBuilderIline').send_keys('Broadcast Welcome_to_PW')
        self._send_console_command()
        self.assertEqual('Broadcasted: Welcome_to_PW', context.get_instance_loglastline())
        self._stop_server()
