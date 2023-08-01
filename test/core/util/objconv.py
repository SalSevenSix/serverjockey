import unittest
from core.util import objconv


class TestCoreUtilObjConv(unittest.TestCase):

    def test_to_bool(self):
        self.assertFalse(objconv.to_bool(False))
        self.assertFalse(objconv.to_bool(None))
        self.assertFalse(objconv.to_bool(0))
        self.assertFalse(objconv.to_bool(0.0))
        self.assertFalse(objconv.to_bool(-1))
        self.assertFalse(objconv.to_bool(-0.1))
        self.assertFalse(objconv.to_bool(''))
        self.assertFalse(objconv.to_bool(' '))
        self.assertFalse(objconv.to_bool('False'))
        self.assertFalse(objconv.to_bool('false'))
        self.assertFalse(objconv.to_bool('no'))
        self.assertFalse(objconv.to_bool('n'))
        self.assertTrue(objconv.to_bool(True))
        self.assertTrue(objconv.to_bool(_TestClass()))
        self.assertTrue(objconv.to_bool('True'))
        self.assertTrue(objconv.to_bool('true'))
        self.assertTrue(objconv.to_bool('yes'))
        self.assertTrue(objconv.to_bool('y'))
        self.assertTrue(objconv.to_bool(1))
        self.assertTrue(objconv.to_bool(1.0))
        self.assertTrue(objconv.to_bool(0.1))

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
        test_object = _TestClass()
        mem_id = repr(test_object).split(' ')[-1][:-1]
        self.assertEqual('_TestClass:' + mem_id, objconv.obj_to_str(test_object))


class _TestClass:
    pass
