import os
import time
from selenium import webdriver as drivers
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from core.util import util
from core.msgc import sc


def _de_increment_wait(wait: float) -> float:
    if wait < 0.0:
        raise Exception('wait timed out')
    time.sleep(1.0)
    wait -= 1.0
    return wait


class _WebTestContext:

    def __init__(self):
        self.driver = drivers.Chrome()
        time.sleep(0.2)
        self.driver.set_window_size(1400, 800)
        self.actions = ActionChains(self.driver)
        self.home = '/'.join(os.getcwd().split('/')[0:3]) + '/serverjockey/'
        self.net_public = self._login()

    def _login(self) -> str:
        self.driver.get('http://localhost:6164')
        login_button = self.find_element('loginModalLogin')
        if not login_button.is_enabled():
            self.find_element('loginModalToken').send_keys('xxxxxxxxxx')
        login_button.click()
        return self.find_element('systemInfoNetPublic', exists=3.0).get_attribute('innerText')

    def clear_notification(self):
        if self.has_element('notificationsText0'):
            self.find_element('notificationsText0').click()
            time.sleep(1.0)

    def goto_home(self):
        self.clear_notification()
        self.find_element('navbarHome').click()
        assert self.find_element('systemInfoVersion', exists=3.0)

    def goto_instances(self):
        self.clear_notification()
        self.find_element('navbarInstances').click()
        time.sleep(1.0)  # for instances to load

    def goto_instance(self, identity: str, module: str):
        self.clear_notification()
        self.find_element('navbarInstances').click()
        self.find_element('instanceListViewI' + identity, by=By.NAME, exists=3.0).click()
        instance_header = self.find_element('instanceHeader', exists=2.0).get_attribute('innerText')
        assert instance_header == identity + ' \xA0\xA0 ' + module

    def goto_guides(self):
        self.clear_notification()
        self.find_element('navbarGuides').click()

    def goto_about(self):
        self.clear_notification()
        self.find_element('navbarAbout').click()

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

    def has_element(self, value: str, by=By.ID) -> bool:
        # noinspection PyBroadException
        try:
            return self.find_element(value, by) is not None
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

    def get_instance_log(self) -> str:
        return self.find_element('consoleLogConsoleLogText').get_attribute('value')

    def check_instance_log(self, limit: int, *contains: str) -> bool:
        log_lines = self.get_instance_log().split('\n')
        log_lines = log_lines[len(log_lines) - limit:]
        for line in log_lines:
            if line in contains:
                return True
        return False

    def get_instance_loglastline(self) -> str:
        return self.get_instance_log().split('\n')[-1]

    def wait_for_instance_state(self, success: str, error: str = sc.EXCEPTION, wait: float = 2.0):
        state = self.find_element('serverStatusState')
        while True:
            value = self.get_instance_state(state)
            if value == success:
                return
            if value == error:
                raise Exception(f'wait for state ended in {error}')
            wait = _de_increment_wait(wait)

    def backup_path(self, instance: str, filename: str = ''):
        return self.home + instance + '/backups/' + filename


_CONTEXT = _WebTestContext()


def get() -> _WebTestContext:
    return _CONTEXT
