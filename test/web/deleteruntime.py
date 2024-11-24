import unittest
from test.web import webcontext


class TestDeleteRuntime(unittest.TestCase):

    def _delete(self, identity: str, module: str):
        # open instance page
        context = webcontext.get()
        context.goto_instance(identity, module)
        context.find_element('collapsibleDeployment').click()
        # delete runtime
        context.find_element('runtimeControlsDelete').click()
        context.find_element('confirmModalConfirm').click()
        self.assertEqual('Delete runtime completed.',
                         context.find_element('notificationsText0', exists=20.0).get_attribute('innerText'))
        # check deleted
        context.find_element('runtimeControlsMeta').click()
        self.assertEqual('Meta not found. No runtime installed.',
                         context.find_element('notificationsText0').get_attribute('innerText'))
        context.find_element('notificationsText1').click()
        context.find_element('notificationsText0').click()

    def test_delete_projectzomboid(self):
        self._delete('pz', 'projectzomboid')

    def test_delete_factorio(self):
        self._delete('ft', 'factorio')

    def test_delete_unturned(self):
        self._delete('ut', 'unturned')

    def test_delete_sevendaystodie(self):
        self._delete('7d2d', 'sevendaystodie')

    def test_delete_starbound(self):
        self._delete('sb', 'starbound')

    def test_delete_palworld(self):
        self._delete('pw', 'palworld')
