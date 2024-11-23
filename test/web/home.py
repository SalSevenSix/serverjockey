import unittest
from test.web import webcontext
from selenium.webdriver.common.by import By


class TestHomePage(unittest.TestCase):

    def test_navigation(self):
        # open home page
        context = webcontext.get()
        context.goto('/')
        # wait for system info
        self.assertIsNotNone(context.find_element('systemInfoUptime', exists=6.0).get_attribute('innerText'))
        # goto projectzomboid instance
        context.find_element('navbarInstances').click()
        context.find_element('instanceListViewIpz', by=By.NAME, exists=2.0).click()
        self.assertEqual('pz \xA0\xA0 projectzomboid',
                         context.find_element('instanceHeader', exists=2.0).get_attribute('innerText'))
