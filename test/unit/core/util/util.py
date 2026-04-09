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

    def test_extract_iproute_adaptor(self):
        self.assertEqual(None, util.extract_iproute_adaptor(None))
        self.assertEqual(None, util.extract_iproute_adaptor(''))
        self.assertEqual(None, util.extract_iproute_adaptor('   \n'))
        self.assertEqual(None, util.extract_iproute_adaptor(b''))
        data = '\n'.join([
          '192.168.1.0/24 dev enp0s3 proto kernel scope link src 192.168.1.8 metric 100',
          'default via 192.168.1.1 dev enp0s3 proto dhcp metric 100',
          '169.254.0.0/16 dev docker0 scope link metric 1000 linkdown',
          '172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown'])
        self.assertEqual('enp0s3', util.extract_iproute_adaptor(data))

    def test_extract_ipaddrshow_ips(self):
        ipv4, ipv6 = util.extract_ipaddrshow_ips(None)
        self.assertEqual(0, len(ipv4) + len(ipv6))
        ipv4, ipv6 = util.extract_ipaddrshow_ips('')
        self.assertEqual(0, len(ipv4) + len(ipv6))
        ipv4, ipv6 = util.extract_ipaddrshow_ips('   \n')
        self.assertEqual(0, len(ipv4) + len(ipv6))
        ipv4, ipv6 = util.extract_ipaddrshow_ips(b'')
        self.assertEqual(0, len(ipv4) + len(ipv6))
        ipv4, ipv6 = util.extract_ipaddrshow_ips('enp0s3           UP             192.168.18/24 2001:53fc/64')
        self.assertEqual(0, len(ipv4) + len(ipv6))
        data = '192.168.1.2/24 192.168.1.8/24 2001::ef1/24 2001:ef0:54b1:8f60:63c4:c232:67e:51fc/64'
        ipv4, ipv6 = util.extract_ipaddrshow_ips('enp0s3           UP             ' + data)
        self.assertEqual(('192.168.1.2', '192.168.1.8'), ipv4)
        self.assertEqual(('2001::ef1', '2001:ef0:54b1:8f60:63c4:c232:67e:51fc'), ipv6)

    def test_fname(self):
        self.assertEqual(None, util.fname(None))
        self.assertEqual('', util.fname(''))
        self.assertEqual('', util.fname('/'))
        self.assertEqual('', util.fname('///'))
        self.assertEqual('', util.fname('/aaa/bbb/ccc/'))
        self.assertEqual('.text', util.fname('/aaa/bbb/ccc/.text'))
        self.assertEqual('.text', util.fname('.text'))
        self.assertEqual('aaa', util.fname('aaa'))
        self.assertEqual('aaa.text', util.fname('aaa.text'))
        self.assertEqual('aaa', util.fname('/aaa'))
        self.assertEqual('aaa.text', util.fname('/aaa.text'))
        self.assertEqual('ccc', util.fname('aaa/bbb/ccc'))
        self.assertEqual('ccc.text', util.fname('aaa/bbb/ccc.text'))
        self.assertEqual('ccc', util.fname('/aaa/bbb/ccc'))
        self.assertEqual('ccc.text', util.fname('/aaa/bbb/ccc.text'))
        self.assertEqual('aa-bb-cc', util.fname('http://foo/bar/aa-bb-cc'))

    def test_fname_only(self):
        self.assertEqual(None, util.fname_only(None))
        self.assertEqual('', util.fname_only(''))
        self.assertEqual('', util.fname_only('/aaa/bbb/ccc/'))
        self.assertEqual('', util.fname_only('/aaa/bbb/ccc/.text'))
        self.assertEqual('', util.fname_only('.text'))
        self.assertEqual('aaa', util.fname_only('aaa'))
        self.assertEqual('aaa', util.fname_only('aaa.text'))
        self.assertEqual('aaa', util.fname_only('/aaa'))
        self.assertEqual('aaa', util.fname_only('/aaa.text'))
        self.assertEqual('ccc', util.fname_only('aaa/bbb/ccc'))
        self.assertEqual('ccc', util.fname_only('aaa/bbb/ccc.text'))
        self.assertEqual('ccc', util.fname_only('/aaa/bbb/ccc'))
        self.assertEqual('ccc', util.fname_only('/aaa/bbb/ccc.text'))

    def test_fext(self):
        self.assertEqual(None, util.fext(None))
        self.assertEqual('', util.fext(''))
        self.assertEqual('', util.fext('/aaa/bbb/ccc/'))
        self.assertEqual('text', util.fext('/aaa/bbb/ccc/.text'))
        self.assertEqual('text', util.fext('.text'))
        self.assertEqual('', util.fext('aaa'))
        self.assertEqual('text', util.fext('aaa.text'))
        self.assertEqual('', util.fext('/aaa'))
        self.assertEqual('text', util.fext('/aaa.text'))
        self.assertEqual('', util.fext('aaa/bbb/ccc'))
        self.assertEqual('text', util.fext('aaa/bbb/ccc.text'))
        self.assertEqual('', util.fext('/aaa/bbb/ccc'))
        self.assertEqual('text', util.fext('/aaa/bbb/ccc.text'))
        self.assertEqual('text', util.fext('/aaa/bbb/ccc.log.text'))

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
