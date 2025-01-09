import unittest
import time
from test.web import webcontext
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from core.util import idutil, objconv, sysutil, dtutil
from core.msgc import sc
from servers.testserver.server import default_config as testserver_default_config


class TestBasics(unittest.TestCase):

    def test_navigation(self):
        context = webcontext.get()
        # goto home
        context.goto_home()
        self.assertEqual(sysutil.system_version(),
                         context.find_element('systemInfoVersion', exists=3.0).get_attribute('innerText'))
        # goto instances
        context.goto_instances()
        self.assertTrue(context.has_element('instanceList'))
        # goto guides
        context.goto_guides()
        # goto about
        context.goto_about()

    def test_create_install_run_delete_instance(self):
        # open instances page
        context, module, identity = webcontext.get(), 'testserver', idutil.generate_id().lower()
        context.goto_instances()
        # create new test server instance
        Select(context.find_element('createInstanceModule')).select_by_value(module)
        context.find_element('createInstanceIdentity').send_keys(identity)
        context.find_element('createInstanceCreate').click()
        context.find_element('instanceListViewI' + identity, by=By.NAME, exists=2.0).click()
        self.assertEqual(identity + ' \xA0\xA0 ' + module,
                         context.find_element('instanceHeader', exists=2.0).get_attribute('innerText'))
        # install runtime
        context.find_element('collapsibleDeployment').click()
        context.find_element('runtimeControlsInstall', enabled=2.0).click()
        context.find_element('confirmModalConfirm').click()
        context.scroll_to_top()
        notification = context.find_element('notificationsText0')
        self.assertEqual('Install Runtime completed.', notification.get_attribute('innerText'))
        notification.click()
        # start server
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state(sc.STARTED, wait=8.0)
        time.sleep(1.0)  # just let the server run a little
        self.assertEqual('1.8.42', context.find_element('serverStatusVersion').get_attribute('innerText'))
        self.assertEqual('101.201.301.404:27001',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
        # stop server
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state(sc.STOPPED, wait=4.0)
        # delete instance
        context.find_element('navbarInstances').click()
        context.find_element('instanceListDeleteI' + identity, by=By.NAME, exists=2.0).click()
        context.find_element('confirmModalName').send_keys(identity)
        context.find_element('confirmModalConfirm').click()
        time.sleep(1.0)  # for instance to delete
        self.assertFalse(context.has_element('instanceListDeleteI' + identity, by=By.NAME))

    def test_chat_logging(self):
        # open instance page
        context, config = webcontext.get(), testserver_default_config()
        config['players'], config['start_speed_modifier'], config['ingametime_interval_seconds'] = '', 0, 0.0
        config, player, message = objconv.obj_to_json(config, pretty=True), 'WebTestPlayer', 'Oh darn it all'
        context.goto_instance('test', 'testserver')
        # set the config to have no players auto-login
        context.find_element('collapsibleConfiguration').click()
        context.find_element('configFileCommandLineArgsClear', exists=2.0, enabled=2.0).click()
        context.find_element('configFileCommandLineArgsText').send_keys(config)
        context.find_element('configFileCommandLineArgsSave').click()
        context.clear_notification()
        context.find_element('collapsibleConfiguration').click()
        # start server
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state(sc.STARTED)
        # run commands
        context.find_element('collapsibleConsoleCommands').click()
        cmd_box, send_btn = context.find_element('commandBuilderIline'), context.find_element('commandBuilderSend')
        cmd_box.send_keys('login ' + player)
        send_btn.click()
        cmd_box.clear()
        context.clear_notification()
        cmd_box.send_keys('kill ' + player)
        send_btn.click()
        cmd_box.clear()
        context.clear_notification()
        cmd_box.send_keys('say ' + player + ' ' + message)
        send_btn.click()
        cmd_box.clear()
        context.clear_notification()
        cmd_box.send_keys('logout ' + player)
        send_btn.click()
        cmd_box.clear()
        context.clear_notification()
        # stop server
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state(sc.STOPPED)
        # confirm chat logging
        context.find_element('collapsibleChatLog').click()
        Select(context.find_element('queryDateRangeChatLogSfromms')).select_by_value('0')
        context.find_element('queryDateRangeChatLogIfromdt').send_keys(dtutil.format_time_standard(time.time() - 60.0))
        context.find_element('queryChatTypesChatLogBoth').click()
        context.find_element('queryExecuteChatLog').click()
        self.assertIsNotNone(context.find_element('chatActivityChatLogList', exists=3.0))
        self.assertEqual(player, context.get_cell_text('chatActivityChatLogList', 2, 2))
        self.assertEqual(sc.LOGIN, context.get_cell_text('chatActivityChatLogList', 2, 3))
        self.assertEqual(player, context.get_cell_text('chatActivityChatLogList', 3, 2))
        self.assertEqual(sc.DEATH, context.get_cell_text('chatActivityChatLogList', 3, 3))
        self.assertEqual(player, context.get_cell_text('chatActivityChatLogList', 4, 2))
        self.assertEqual(message, context.get_cell_text('chatActivityChatLogList', 4, 3))
        self.assertEqual(player, context.get_cell_text('chatActivityChatLogList', 5, 2))
        self.assertEqual(sc.LOGOUT, context.get_cell_text('chatActivityChatLogList', 5, 3))

    def test_restart_immediately(self):
        # start server
        context = webcontext.get()
        context.goto_instance('test', 'testserver')
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state(sc.STARTED)
        # restart
        context.find_element('consoleLogConsoleLogClear').click()
        context.find_element('serverControlsRestart').click()
        context.find_element('serverControlsRestartOptionImmediately').click()
        time.sleep(1.0)
        context.wait_for_instance_state(sc.STARTED)
        # check log to confirm restart actually happened
        logtext = context.get_instance_log().strip().split('\n')
        self.assertTrue(len(logtext) > 0, 'Expected more logging')
        self.assertEqual('### Received STDIN: quit', logtext[0])
        while len(logtext) > 0:
            if '### *** SERVER STARTED ***' == logtext.pop():
                break
        self.assertTrue(len(logtext) > 0, 'Expected server to be STARTED but was not')
        # stop server
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state(sc.STOPPED)

    def test_restart_after_warnings(self):
        # start server
        context = webcontext.get()
        context.goto_instance('test', 'testserver')
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state(sc.STARTED)
        # restart
        context.find_element('consoleLogConsoleLogClear').click()
        context.find_element('serverControlsRestart').click()
        context.find_element('serverControlsRestartOptionAfterWarnings').click()
        self.assertEqual('Server restarting after warning players.',
                         context.find_element('notificationsText0').get_attribute('innerText'))
        # check warnings
        time.sleep(1.0)
        self.assertEqual('### Broadcast "Server restart in 30 seconds."', context.get_instance_loglastline())
        time.sleep(20.0)
        self.assertEqual('### Broadcast "Server restart in 10 seconds."', context.get_instance_loglastline())
        context.find_element('consoleLogConsoleLogClear').click()
        time.sleep(10.0)
        context.wait_for_instance_state(sc.STARTED)
        # check log to confirm restart actually happened
        logtext = context.get_instance_log().strip().split('\n')
        self.assertTrue(len(logtext) > 0, 'Expected more logging')
        self.assertEqual('### Received STDIN: quit', logtext[0])
        while len(logtext) > 0:
            if '### *** SERVER STARTED ***' == logtext.pop():
                break
        self.assertTrue(len(logtext) > 0, 'Expected server to be STARTED but was not')
        # stop server
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state(sc.STOPPED)

    def test_restart_on_empty(self):
        # open instance page
        context, config = webcontext.get(), testserver_default_config()
        config['players'], config['start_speed_modifier'], config['ingametime_interval_seconds'] = 'TheOne', 0, 0.0
        config = objconv.obj_to_json(config, pretty=True)
        context.goto_instance('test', 'testserver')
        # set the config to have one player login
        context.find_element('collapsibleConfiguration').click()
        context.find_element('configFileCommandLineArgsClear', exists=2.0, enabled=2.0).click()
        context.find_element('configFileCommandLineArgsText').send_keys(config)
        context.find_element('configFileCommandLineArgsSave').click()
        context.clear_notification()
        context.find_element('collapsibleConfiguration').click()
        # start server
        context.find_element('serverControlsStart').click()
        context.wait_for_instance_state(sc.STARTED)
        # restart
        context.find_element('consoleLogConsoleLogClear').click()
        context.find_element('serverControlsRestart').click()
        context.find_element('serverControlsRestartOptionOnEmpty').click()
        self.assertEqual('Server restarting when empty.',
                         context.find_element('notificationsText0').get_attribute('innerText'))
        context.clear_notification()
        # check not restarting
        time.sleep(1.0)
        self.assertEqual('', context.get_instance_log())
        # logout player
        context.find_element('collapsibleConsoleCommands').click()
        context.find_element('commandBuilderIline').send_keys('logout TheOne')
        context.find_element('commandBuilderSend').click()
        context.clear_notification()
        time.sleep(1.0)
        context.wait_for_instance_state(sc.STARTED)
        # check log to confirm restart actually happened
        logtext = context.get_instance_log().strip().split('\n')
        self.assertTrue(len(logtext) > 0, 'Expected more logging')
        self.assertEqual('### Received STDIN: quit', logtext[2])
        while len(logtext) > 0:
            if '### *** SERVER STARTED ***' == logtext.pop():
                break
        self.assertTrue(len(logtext) > 0, 'Expected server to be STARTED but was not')
        # stop server
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state(sc.STOPPED)
