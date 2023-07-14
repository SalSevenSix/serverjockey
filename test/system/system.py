import unittest
from test.system import systest


class TestSystem(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        await systest.setup()

    async def test_get_modules(self):
        result = await systest.get('/modules')
        self.assertEqual(5, len(result))
        self.assertTrue('projectzomboid' in result)
        self.assertTrue('factorio' in result)
        self.assertTrue('sevendaystodie' in result)
        self.assertTrue('unturned' in result)
        self.assertTrue('starbound' in result)
