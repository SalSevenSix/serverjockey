from yarl import URL
from core.util import util
from core.http import httprsc


def test():
    test_only_one_arg_allowed()
    test_basic_build_path()
    test_basic_path_arg()
    test_tail_path_cannot_psh_children()
    test_tail_path_cannot_put_children()
    test_tail_path_arg()
    test_tail_build_path()


def test_only_one_arg_allowed():
    builder = httprsc.ResourceBuilder(httprsc.WebResource())
    try:
        builder.psh('a').put('{b}').put('x{c}')
    except Exception as e:
        print(util.obj_to_str(e))
        return
    raise Exception('test_only_one_arg_allowed()')


def test_basic_build_path():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).psh('foo').psh('{key}').put('bar')
    resource = root.lookup(URL('http://localhost:6164/foo/value/bar').path)
    processor = httprsc.PathProcessor(resource)
    assert '/foo/key/bar' == processor.build_path()
    assert '/foo/xxx/bar' == processor.build_path({'key': 'xxx'})


def test_basic_path_arg():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).psh('foo').psh('{key}').psh('bar').put('xyz')
    url = URL('http://localhost:6164/foo/value/bar')
    resource = root.lookup(url.path)
    processor = httprsc.PathProcessor(resource)
    data = processor.extract_args_url(url)
    assert 'value' == data['key']


def test_tail_path_cannot_psh_children():
    builder = httprsc.ResourceBuilder(httprsc.WebResource())
    builder.psh('a').psh('*{b}')
    try:
        builder.psh('c')
    except Exception as e:
        print(util.obj_to_str(e))
        return
    raise Exception('test_tail_path_cannot_psh_children()')


def test_tail_path_cannot_put_children():
    builder = httprsc.ResourceBuilder(httprsc.WebResource())
    builder.psh('a').psh('*{b}')
    try:
        builder.put('c')
    except Exception as e:
        print(util.obj_to_str(e))
        return
    raise Exception('test_tail_path_cannot_put_children()')


def test_tail_path_arg():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).psh('foo').psh('{bar}').put('*{tail}')
    url = URL('http://localhost:6164/foo/xyz/a/b/c')
    resource = root.lookup(url.path)
    data = httprsc.PathProcessor(resource).extract_args_url(url)
    assert 'xyz' == data['bar']
    assert 'a/b/c' == data['tail']


def test_tail_build_path():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).psh('foo').psh('{bar}').put('*{tail}')
    url = URL('http://localhost:6164/foo/xyz/a/b/c')
    resource = root.lookup(url.path)
    assert '/foo/bar' == resource.path()
    assert '/foo/yay/x/y/z' == resource.path({'bar': 'yay', 'tail': 'x/y/z'})


if __name__ == '__main__':
    test()
