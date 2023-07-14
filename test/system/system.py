import unittest
# from core.util import objconv
# from test.system import systest


class TestSystem(unittest.IsolatedAsyncioTestCase):

    async def test_get_modules(self):
        pass
        # result = await systest.get('/modules')
        # self.assertEqual(5, len(result))
        # self.assertTrue('projectzomboid' in result)
        # self.assertTrue('factorio' in result)
        # self.assertTrue('sevendaystodie' in result)
        # self.assertTrue('unturned' in result)
        # self.assertTrue('starbound' in result)

    async def test_get_instances(self):
        pass
        # self.assertEqual(objconv.json_to_dict(_expected_get_instances()), await systest.get('/instances'))


def _expected_get_instances():
    return '''{"7d2d": {"module": "sevendaystodie",
          "url": "http://localhost:6164/instances/7d2d"},
 "ft": {"module": "factorio", "url": "http://localhost:6164/instances/ft"},
 "pz": {"module": "projectzomboid",
        "url": "http://localhost:6164/instances/pz"},
 "sb": {"module": "starbound", "url": "http://localhost:6164/instances/sb"},
 "ut": {"module": "unturned", "url": "http://localhost:6164/instances/ut"}}'''
