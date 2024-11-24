import os
import time
from core.util import util
from selenium import webdriver as drivers
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

_BASE_URL = 'http://localhost:6164'


def _de_increment_wait(wait: float) -> float:
    if wait < 0.0:
        raise Exception('wait timed out')
    time.sleep(1.0)
    wait -= 1.0
    return wait


class _WebTestContext:

    def __init__(self):
        self.driver = drivers.Chrome()
        self.driver.set_window_size(1280, 720)
        self.actions = ActionChains(self.driver)
        self.home = '/'.join(os.getcwd().split('/')[0:3]) + '/serverjockey/'
        self.path, self.net_public = None, None

    def goto(self, path: str = '/'):
        if path == self.path:
            return
        if self.path:
            self.driver.get(_BASE_URL + path)
            self.path = path
            return
        self.driver.get(_BASE_URL)
        login_button = self.find_element('loginModalLogin')
        if not login_button.is_enabled():
            self.find_element('loginModalToken').send_keys('xxxxxxxxxx')
            assert login_button.is_enabled()
        login_button.click()
        self.net_public = self.find_element('systemInfoNetPublic', exists=6.0).get_attribute('innerText')
        self.path = '/'
        self.goto(path)

    def goto_instance(self, identity: str, module: str):
        if not self.path:
            self.goto()
        self.find_element('navbarInstances').click()
        self.find_element('instanceListViewI' + identity, by=By.NAME, exists=3.0).click()
        instance_header = self.find_element('instanceHeader', exists=2.0).get_attribute('innerText')
        assert instance_header == identity + ' \xA0\xA0 ' + module

    def scroll_to_top(self):
        self.actions.send_keys(Keys.HOME).perform()

    def find_element(self, value: str, by=By.ID,
                     exists: float = 0.0, displayed: float = 0.0, enabled: float = 0.0) -> WebElement:
        if exists and exists > 0.0:
            WebDriverWait(self.driver, timeout=exists).until(lambda x: self.driver.find_element(by=by, value=value))
        element = self.driver.find_element(by=by, value=value)
        if displayed and displayed > 0.0:
            WebDriverWait(self.driver, timeout=displayed).until(lambda x: element.is_displayed())
        if enabled and enabled > 0.0:
            WebDriverWait(self.driver, timeout=enabled).until(lambda x: element.is_enabled())
        return element

    def has_element(self, value: str) -> bool:
        # noinspection PyBroadException
        try:
            return self.find_element(value) is not None
        except Exception:
            return False

    def get_cell_text(self, aid: str, row: int, col: int) -> str:
        result = self.find_element('//tbody[@id="' + aid + '"]/tr[' + str(row) + ']/td[' + str(col) + ']', by=By.XPATH)
        result = result.get_attribute('innerText').replace('\xA0', '').strip()
        return result

    def get_instance_state(self, state: WebElement = None) -> str:
        if not state:
            state = self.find_element('serverStatusState')
        result = state.get_attribute('innerText')
        result = result.replace('\xA0', '').replace(' ', '')
        result = util.rchop(result, '(')
        return result

    def get_instance_loglastline(self) -> str:
        return self.find_element('consoleLogConsoleLogText').get_attribute('value').split('\n')[-1]

    def wait_for_instance_state(self, success: str, error: str = 'EXCEPTION', wait: float = 2.0):
        state = self.find_element('serverStatusState')
        success, error = success.upper(), error.upper() if error else None
        while True:
            value = self.get_instance_state(state)
            if value == success:
                return
            if value == error:
                raise Exception('wait for state ended in ' + error)
            wait = _de_increment_wait(wait)

    def backup_path(self, instance: str, filename: str = ''):
        return self.home + instance + '/backups/' + filename


_CONTEXT = _WebTestContext()


def get() -> _WebTestContext:
    return _CONTEXT
