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
        self.assertEqual('http://foo.bar:6164/aaa/bbb', util.build_url(host='foo.bar', port=6164, path='/aaa/bbb'))
        self.assertEqual('http://foo.bar/a?x=y&a=b', util.build_url(host='foo.bar', path='/a?x=y&a=b'))
        self.assertEqual('http://foo.bar/aaa/bbb',
                         util.build_url(scheme='http', host='foo.bar', port=80, path='/aaa/bbb'))
        self.assertEqual('https://foo.bar:80/aaa/bbb',
                         util.build_url(scheme='https', host='foo.bar', port=80, path='/aaa/bbb'))
        self.assertEqual('https://foo.bar/aaa/bbb',
                         util.build_url(scheme='https', host='foo.bar', port=443, path='/aaa/bbb'))
        self.assertEqual('http://foo.bar:443/aaa/bbb',
                         util.build_url(scheme='http', host='foo.bar', port=443, path='/aaa/bbb'))
        self.assertEqual('https://foo.bar:6164/aaa/bbb',
                         util.build_url(scheme='https', host='foo.bar', port=6164, path='/aaa/bbb'))

    def test_keyfill_dict(self):
        template = dict(numb=123, text='abc', data=dict(aaa=123, bbb='xyz'))
        dictionary = dict(numb=456, text='xyz', data=dict(aaa=789, bbb='gjh'))
        actual = util.keyfill_dict(dictionary, template, True)
        self.assertIs(dictionary, actual, 'No change')
        dictionary = dict(numb=456, data=dict(bbb='gjh'))
        actual = util.keyfill_dict(dictionary, template, True)
        expected = dict(numb=456, data=dict(bbb='gjh', aaa=123), text='abc')
        self.assertIsNot(expected, actual, 'Deep copy is not')
        self.assertEqual(expected, actual, 'Deep copy equals')
        actual = util.keyfill_dict(dictionary, template, False)
        expected = dict(numb=456, data=dict(bbb='gjh'), text='abc')
        self.assertIsNot(expected, actual, 'Shallow copy is not')
        self.assertEqual(expected, actual, 'Shallow copy equals')

    def test_lchop(self):
        self.assertEqual('', util.lchop('', ''))
        self.assertEqual('hey yo }) the end bit', util.lchop('Hello world ({ hey yo }) the end bit ', '({'))
        self.assertEqual(' hey yo }) the end bit ', util.lchop('Hello world ({ hey yo }) the end bit ', '({', False))

    def test_rchop(self):
        self.assertEqual('', util.rchop('', ''))
        self.assertEqual('Hello world ({ hey yo', util.rchop(' Hello world ({ hey yo }) the end bit', '})'))
        self.assertEqual(' Hello world ({ hey yo ', util.rchop(' Hello world ({ hey yo }) the end bit', '})', False))

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

    def test_extract_hostname_ips(self):
        result = util.extract_hostname_ips(None)
        self.assertEqual(0, len(result[0]))
        self.assertEqual(0, len(result[1]))
        result = util.extract_hostname_ips('')
        self.assertEqual(0, len(result[0]))
        self.assertEqual(0, len(result[1]))
        result = util.extract_hostname_ips('   \n')
        self.assertEqual(0, len(result[0]))
        self.assertEqual(0, len(result[1]))
        result = util.extract_hostname_ips(b'')
        self.assertEqual(0, len(result[0]))
        self.assertEqual(0, len(result[1]))
        result = util.extract_hostname_ips('fe80::a66b:e8e4:cfe3:cf20')
        self.assertEqual(0, len(result[0]))
        self.assertEqual(0, len(result[1]))
        result = util.extract_hostname_ips('10.0.0.192 2603:c024:4512:c301:23d0:bce:cdc9:b87a')
        self.assertEqual(('10.0.0.192',), result[0])
        self.assertEqual(('2603:c024:4512:c301:23d0:bce:cdc9:b87a', ), result[1])
        result = util.extract_hostname_ips('10.0.0.251 172.17.0.1')
        self.assertEqual(('10.0.0.251', '172.17.0.1'), result[0])
        self.assertEqual(0, len(result[1]))
        result = util.extract_hostname_ips('192.168.156.76')
        self.assertEqual(('192.168.156.76',), result[0])
        self.assertEqual(0, len(result[1]))

    def test_fname(self):
        self.assertEqual(None, util.fname(None))
        self.assertEqual('', util.fname(''))
        self.assertEqual('', util.fname('/'))
        self.assertEqual('', util.fname('///'))
        self.assertEqual('', util.fname('/aaa/bbb/ccc/'))
        self.assertEqual('aaa', util.fname('aaa'))
        self.assertEqual('aaa', util.fname('/aaa'))
        self.assertEqual('ccc', util.fname('aaa/bbb/ccc'))
        self.assertEqual('ccc', util.fname('/aaa/bbb/ccc'))
        self.assertEqual('aa-bb-cc', util.fname('http://foo/bar/aa-bb-cc'))

    def test_single(self):
        self.assertEqual(None, util.single(None))
        self.assertEqual(None, util.single([]))
        self.assertEqual(1, util.single([1]))
        self.assertEqual(1, util.single([1, 2]))

    def test_fill(self):
        self.assertEqual((None, None, None), util.fill(None, 3))
        self.assertEqual((None, None, None), util.fill([], 3))
        self.assertEqual((1, None, None), util.fill([1], 3))
        self.assertEqual((1, 2, None), util.fill([1, 2], 3))
        self.assertEqual((1, 2, 3), util.fill([1, 2, 3], 3))
        self.assertEqual((1, 2, 3, 4), util.fill([1, 2, 3, 4], 3))
