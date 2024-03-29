import unittest
from yarl import URL
from core.util import util


class TestCoreUtilUtil(unittest.TestCase):

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

    def test_test_url(self):
        url = URL('test:///path/file.html?foo=bar&a=b')
        self.assertEqual('test', url.scheme)
        self.assertEqual(None, url.host)
        self.assertEqual(None, url.port)
        self.assertEqual('/path/file.html', url.path)
        self.assertEqual('foo=bar&a=b', url.query_string)

    def test_build_url(self):
        self.assertEqual('test:///path/resource', util.build_url('test', None, None, 'path/resource'))
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

    def test_human_file_size(self):
        self.assertEqual('', util.human_file_size(None))
        self.assertEqual('0 B', util.human_file_size(0))
        self.assertEqual('512 B', util.human_file_size(512))
        self.assertEqual('1023 B', util.human_file_size(1023))
        self.assertEqual('1.0 KiB', util.human_file_size(1024))
        self.assertEqual('1.5 KiB', util.human_file_size(512 * 3))
        self.assertEqual('1.0 MiB', util.human_file_size(1024 * 1024))
        self.assertEqual('1.2 MiB', util.human_file_size(int(1024 * 1024 * 1.2)))
        self.assertEqual('1.0 GiB', util.human_file_size(1024 * 1024 * 1024))
        self.assertEqual('1.0 TiB', util.human_file_size(1024 * 1024 * 1024 * 1024))

    def test_split_lines(self):
        self.assertEqual(('aaa', 'bbb', 'ccc'), util.split_lines('aaa\nbbb\nccc'))
        self.assertEqual(None, util.split_lines('aaa\nbbb\nccc', lines_limit=2))
        self.assertEqual(('aaa', 'bbb', 'ccc'), util.split_lines('aaa\nbbb\nccc', lines_limit=3))
        self.assertEqual(None, util.split_lines('aaa\nbbb\nccc', line_char_limit=2))
        self.assertEqual(('aaa', 'bbb', 'ccc'), util.split_lines('aaa\nbbb\nccc', line_char_limit=3))
        self.assertEqual(None, util.split_lines('aaa\nbbb\nccc', total_char_limit=10))
        self.assertEqual(('aaa', 'bbb', 'ccc'), util.split_lines('aaa\nbbb\nccc', total_char_limit=11))

    def test_full_path(self):
        self.assertEqual(None, util.full_path(None, None))
        self.assertEqual(None, util.full_path('', ''))
        self.assertEqual(None, util.full_path('/home', None))
        self.assertEqual(None, util.full_path('/home', ''))
        self.assertEqual('/home', util.full_path('/home', '.'))
        self.assertEqual('/home', util.full_path('/home/', '.'))
        self.assertEqual('/', util.full_path('/home', '/'))
        self.assertEqual('/path/file.txt', util.full_path(None, '/path/file.txt'))
        self.assertEqual('/path/file.txt', util.full_path('', '/path/file.txt'))
        self.assertEqual('/path/file.txt', util.full_path(None, './path/file.txt'))
        self.assertEqual('/path/file.txt', util.full_path(None, 'path/file.txt'))
        self.assertEqual('/path/file.txt', util.full_path('', 'path/file.txt'))
        self.assertEqual('/path/file.txt', util.full_path('/home', '/path/file.txt'))
        self.assertEqual('/home/path/file.txt', util.full_path('/home', './path/file.txt'))
        self.assertEqual('/home/path/file.txt', util.full_path('/home', 'path/file.txt'))
        self.assertEqual('/home/path/file.txt', util.full_path('/home/', './path/file.txt'))
        self.assertEqual('/home/path/file.txt', util.full_path('/home/', 'path/file.txt'))
        self.assertEqual('/home/.file.txt', util.full_path('/home', '.file.txt'))
        self.assertEqual('/path/', util.full_path(None, 'path/'))
        self.assertEqual('/home/path/', util.full_path('/home', 'path/'))
        self.assertEqual('/path/', util.full_path('/home', '/path/'))
