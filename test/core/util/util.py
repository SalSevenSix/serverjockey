import unittest
from core.util import util


class TestCoreUtil(unittest.TestCase):

    def test_base64_coding(self):
        value = 'So?<p> $ – _ . + ! * ‘ ( ) , [ ] { } | \\ " % ~ # < >'
        encoded = util.urlsafe_b64encode(value)
        self.assertEqual(0, encoded.count('+'))
        self.assertEqual(0, encoded.count('/'))
        self.assertEqual(value, util.urlsafe_b64decode(encoded))

    def test_script_escape(self):
        self.assertEqual('iwbums build14', util.script_escape('iwbums build14'))
        self.assertEqual('1.8.3', util.script_escape('1.8.3'))
        self.assertEqual(r'\#\$\*\&', util.script_escape('#$*&'))

    def test_build_url(self):
        self.assertEqual('http://foo.bar', util.build_url(host='foo.bar'))
        self.assertEqual('http://foo.bar/', util.build_url(host='foo.bar', path='/'))
        self.assertEqual('http://foo.bar/aaa/bbb', util.build_url(host='foo.bar', path='aaa/bbb'))
        self.assertEqual('http://foo.bar/aaa/bbb', util.build_url(host='foo.bar', path='/aaa/bbb'))
        self.assertEqual('http://foo.bar/aaa/bbb', util.build_url(host='foo.bar', port=80, path='/aaa/bbb'))
        self.assertEqual('http://foo.bar:6164/aaa/bbb', util.build_url(host='foo.bar', port=6164, path='/aaa/bbb'))
        self.assertEqual('http://foo.bar/a?x=y&a=b', util.build_url(host='foo.bar', path='/a?x=y&a=b'))
        self.assertEqual('https://foo.bar:6164/aaa/bbb',
                         util.build_url(scheme='https', host='foo.bar', port=6164, path='/aaa/bbb'))

    def test_left_chop_and_strip(self):
        self.assertEqual('', util.left_chop_and_strip('', ''))
        self.assertEqual('hey yo }) the end bit',
                         util.left_chop_and_strip('Hello world ({ hey yo }) the end bit', '({'))

    def test_right_chop_and_strip(self):
        self.assertEqual('', util.right_chop_and_strip('', ''))
        self.assertEqual('Hello world ({ hey yo',
                         util.right_chop_and_strip('Hello world ({ hey yo }) the end bit', '})'))
