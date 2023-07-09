import unittest
from yarl import URL
from core.http import httprsc


class TestCoreUtil(unittest.TestCase):

    def test_only_one_arg_allowed(self):
        builder = httprsc.ResourceBuilder(httprsc.WebResource())
        builder.psh('a').put('{b}')
        with self.assertRaises(Exception):
            builder.put('x{c}')

    def test_basic_build_path(self):
        root = httprsc.WebResource()
        httprsc.ResourceBuilder(root).psh('foo').psh('{key}').put('bar')
        resource = root.lookup(URL('http://localhost:6164/foo/value/bar').path)
        processor = httprsc.PathProcessor(resource)
        self.assertEqual('/foo/key/bar', processor.build_path())
        self.assertEqual('/foo/xxx/bar', processor.build_path({'key': 'xxx'}))

    def test_basic_path_arg(self):
        root = httprsc.WebResource()
        httprsc.ResourceBuilder(root).psh('foo').psh('{key}').psh('bar').put('xyz')
        url = URL('http://localhost:6164/foo/value/bar')
        resource = root.lookup(url.path)
        processor = httprsc.PathProcessor(resource)
        data = processor.extract_args_url(url)
        self.assertEqual('value', data['key'])

    def test_tail_path_cannot_psh_children(self):
        builder = httprsc.ResourceBuilder(httprsc.WebResource())
        builder.psh('a').psh('*{b}')
        with self.assertRaises(Exception):
            builder.psh('c')

    def test_tail_path_cannot_put_children(self):
        builder = httprsc.ResourceBuilder(httprsc.WebResource())
        builder.psh('a').psh('*{b}')
        with self.assertRaises(Exception):
            builder.put('c')

    def test_tail_path_arg(self):
        root = httprsc.WebResource()
        httprsc.ResourceBuilder(root).psh('foo').psh('{bar}').put('*{tail}')
        url = URL('http://localhost:6164/foo/xyz/a/b/c')
        resource = root.lookup(url.path)
        data = httprsc.PathProcessor(resource).extract_args_url(url)
        self.assertEqual('xyz', data['bar'])
        self.assertEqual('a/b/c', data['tail'])

    def test_tail_build_path(self):
        root = httprsc.WebResource()
        httprsc.ResourceBuilder(root).psh('foo').psh('{bar}').put('*{tail}')
        url = URL('http://localhost:6164/foo/xyz/a/b/c')
        resource = root.lookup(url.path)
        self.assertEqual('/foo/bar', resource.path())
        self.assertEqual('/foo/yay/x/y/z', resource.path({'bar': 'yay', 'tail': 'x/y/z'}))
