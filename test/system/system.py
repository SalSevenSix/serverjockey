import unittest
from test.system import systemcontext
from core.util import objconv


class TestSystem(unittest.IsolatedAsyncioTestCase):

    async def test_get_modules(self):
        result = await systemcontext.get('/modules')
        self.assertEqual(9, len(result))
        self.assertTrue('testserver' in result)
        self.assertTrue('projectzomboid' in result)
        self.assertTrue('factorio' in result)
        self.assertTrue('sevendaystodie' in result)
        self.assertTrue('unturned' in result)
        self.assertTrue('starbound' in result)
        self.assertTrue('csii' in result)
        self.assertTrue('palworld' in result)
        self.assertTrue('valheim' in result)

    async def test_get_instances(self):
        self.assertEqual(objconv.json_to_dict(_expected_get_instances()), await systemcontext.get('/instances'))


def _expected_get_instances():
    return '{"testserver": {"module": "testserver", "running": false, "url": "test:///instances/testserver"}}'
