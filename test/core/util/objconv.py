import unittest
from core.util import objconv


class TestCoreObjConversion(unittest.TestCase):

    def test_obj_to_str(self):
        self.assertEqual('None', objconv.obj_to_str(None))
        self.assertEqual('True', objconv.obj_to_str(True))
        self.assertEqual('123', objconv.obj_to_str(123))
        self.assertEqual('1.23', objconv.obj_to_str(1.23))
        self.assertEqual('123', objconv.obj_to_str(123))
        self.assertEqual("'string'", objconv.obj_to_str('string'))
        self.assertEqual('(1, \'a\', True)', objconv.obj_to_str((1, 'a', True)))
        self.assertEqual('[1, \'a\', True]', objconv.obj_to_str([1, 'a', True]))
        self.assertEqual("{'aaa': 1, 'bbb': 'a', 'ccc': True, 'ddd': [1, 'a', True]}",
                         objconv.obj_to_str({'aaa': 1, 'bbb': 'a', 'ccc': True, 'ddd': [1, 'a', True]}))
        test_object = TestClass()
        mem_id = repr(test_object).split(' ')[-1][:-1]
        self.assertEqual('TestClass:' + mem_id, objconv.obj_to_str(test_object))


class TestClass:
    pass
