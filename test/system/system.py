import unittest
from core.util import objconv
from test.system import systest


class TestSystem(unittest.IsolatedAsyncioTestCase):

    async def test_get_modules(self):
        result = await systest.get('/modules')
        self.assertEqual(8, len(result))
        self.assertTrue('testserver' in result)
        self.assertTrue('projectzomboid' in result)
        self.assertTrue('factorio' in result)
        self.assertTrue('sevendaystodie' in result)
        self.assertTrue('unturned' in result)
        self.assertTrue('starbound' in result)
        self.assertTrue('csii' in result)
        self.assertTrue('palworld' in result)

    async def test_get_instances(self):
        self.assertEqual(objconv.json_to_dict(_expected_get_instances()), await systest.get('/instances'))


def _expected_get_instances():
    return '{"testserver": {"module": "testserver", "running": false, "url": "test:///instances/testserver"}}'
