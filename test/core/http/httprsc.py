from yarl import URL
from core.util import util
from core.http import httprsc


def test_only_one_arg_allowed():
    builder = httprsc.ResourceBuilder(httprsc.WebResource())
    try:
        builder.push('a').append('{b}').append('x{c}')
    except Exception as e:
        print(util.obj_to_str(e))


def test_basic_build_path():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).push('foo').push('{key}').append('bar')
    url = URL('http://localhost:6164/foo/value/bar')
    resource = root.lookup(url.path)
    print(httprsc.PathProcessor(resource).build_path())
    print(httprsc.PathProcessor(resource).build_path({'key': 'new_value'}))


def test_basic_path_arg():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).push('foo').push('{key}').push('bar').append('xyz')
    url = URL('http://localhost:6164/foo/value/bar/xyz')
    resource = root.lookup(url.path)
    data = httprsc.PathProcessor(resource).extract_args_url(url)
    print(util.obj_to_json(data))


def test_tail_path_cannot_have_children():
    builder = httprsc.ResourceBuilder(httprsc.WebResource())
    builder.push('a').append('{*}').pop()
    try:
        builder.push('b').push('{*}')
    except Exception as e:
        print(util.obj_to_str(e))


def test_tail_path_arg():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).push('foo').push('{bar}').append('*{tail}')
    url = URL('http://localhost:6164/foo/xyz/a/b/c')
    resource = root.lookup(url.path)
    data = httprsc.PathProcessor(resource).extract_args_url(url)
    print(util.obj_to_json(data))


def test_tail_build_path():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).push('foo').push('{bar}').append('*{tail}')
    url = URL('http://localhost:6164/foo/xyz/a/b/c')
    resource = root.lookup(url.path)
    print(resource.path())
    print(resource.path({'bar': 'yay', 'tail': 'x/y/z'}))


if __name__ == '__main__':
    test_only_one_arg_allowed()
    test_basic_build_path()
    test_basic_path_arg()
    test_tail_path_cannot_have_children()
    test_tail_path_arg()
    test_tail_build_path()
