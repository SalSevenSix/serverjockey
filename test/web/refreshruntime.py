import unittest
import os
from test.web import webcontext
from selenium.webdriver.common.by import By

from servers.projectzomboid.deployment import APPID as APPID_PROJECTZOMBOID
from servers.sevendaystodie.deployment import APPID as APPID_SEVENDAYSTODIE
from servers.unturned.deployment import APPID as APPID_UNTURNED
from servers.starbound.deployment import APPID as APPID_STARBOUND
from servers.palworld.deployment import APPID as APPID_PALWORLD

TEST_BACKUP = 'runtime-webtest.zip'


class TestRefreshRuntime(unittest.TestCase):

    def _refresh(self, identity: str, module: str, appid: str = None, weight: float = 1.0):
        # open instance page
        context = webcontext.get()
        context.goto_instance(identity, module)
        self.assertTrue(context.get_instance_state() in ('READY', 'STOPPED'))
        context.find_element('collapsibleDeployment').click()
        if appid is None:
            # update runtime not steam
            context.find_element('runtimeControlsInstall', enabled=2.0).click()
            context.find_element('confirmModalConfirm').click()
            context.wait_for_instance_state('MAINTENANCE')
            context.scroll_to_top()
            context.wait_for_instance_state('READY', wait=100.0 * weight)
            self.assertEqual('END Install', context.get_instance_loglastline())
            return
        # restore last runtime backup
        context.find_element('collapsibleBackups').click()
        context.find_element('fileSystemBackupsActionE' + TEST_BACKUP, by=By.NAME, exists=3.0).click()
        context.find_element('confirmModalConfirm').click()
        context.wait_for_instance_state('MAINTENANCE')
        context.scroll_to_top()
        context.wait_for_instance_state('READY', wait=100.0 * weight)
        self.assertEqual('END Unpack Directory', context.get_instance_loglastline())
        # update runtime steam
        context.find_element('runtimeControlsInstall', enabled=2.0).click()
        context.find_element('confirmModalConfirm').click()
        context.wait_for_instance_state('MAINTENANCE')
        context.scroll_to_top()
        context.wait_for_instance_state('READY', wait=300.0 * weight)
        self.assertTrue(context.check_instance_log(
            6, 'Success! App \'' + appid + '\' fully installed.',
            'Error! App \'' + appid + '\' state is 0x10C after update job.',
            'Error! App \'' + appid + '\' state is 0x6 after update job.'))
        # refresh last runtime backup
        context.find_element('backupRestoreActionsBackupRuntime').click()
        context.wait_for_instance_state('MAINTENANCE')
        context.scroll_to_top()
        context.wait_for_instance_state('READY', wait=300.0 * weight)
        self.assertEqual('END Archive Directory', context.get_instance_loglastline())
        old_backup = context.backup_path(identity, TEST_BACKUP)
        self.assertTrue(os.path.isfile(old_backup))
        new_backup = context.backup_path(identity, context.get_cell_text('fileSystemBackupsFiles', 1, 2))
        self.assertTrue(os.path.isfile(new_backup))
        os.remove(old_backup)
        os.rename(new_backup, old_backup)

    def test_refresh_projectzomboid(self):
        self._refresh('pz', 'projectzomboid', APPID_PROJECTZOMBOID)

    def test_refresh_factorio(self):
        self._refresh('ft', 'factorio')

    def test_refresh_unturned(self):
        self._refresh('ut', 'unturned', APPID_UNTURNED, weight=1.5)

    def test_refresh_sevendaystodie(self):
        self._refresh('7d2d', 'sevendaystodie', APPID_SEVENDAYSTODIE, weight=2.5)

    def test_refresh_starbound(self):
        self._refresh('sb', 'starbound', APPID_STARBOUND)

    def test_refresh_palworld(self):
        self._refresh('pw', 'palworld', APPID_PALWORLD)
