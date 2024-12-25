import unittest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from test.web import webcontext
from core.util import idutil, sysutil


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
        context.wait_for_instance_state('STARTED', wait=8.0)
        time.sleep(1.0)  # just let the server run a little
        self.assertEqual('1.8.42', context.find_element('serverStatusVersion').get_attribute('innerText'))
        self.assertEqual('101.201.301.404:27001',
                         context.find_element('serverStatusConnect').get_attribute('innerText'))
        # stop server
        context.find_element('serverControlsStop').click()
        context.wait_for_instance_state('STOPPED', wait=4.0)
        # delete instance
        context.find_element('navbarInstances').click()
        context.find_element('instanceListDeleteI' + identity, by=By.NAME, exists=2.0).click()
        context.find_element('confirmModalName').send_keys(identity)
        context.find_element('confirmModalConfirm').click()
        time.sleep(1.0)  # for instance to delete
        self.assertFalse(context.has_element('instanceListDeleteI' + identity, by=By.NAME))
