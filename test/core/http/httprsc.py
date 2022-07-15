import asyncio
from yarl import URL
from core.util import util
from core.http import httprsc


def test_basic_path_arg():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).push('foo').append('{bar}')
    url = URL('http://localhost:6164/foo/yay')
    resource = root.lookup(url.path)
    data = httprsc.PathProcessor(resource).extract_args(url)
    print(util.obj_to_json(data))


def test_tail_path_arg():
    root = httprsc.WebResource()
    httprsc.ResourceBuilder(root).push('foo').append('{/}')
    url = URL('http://localhost:6164/foo/a/b/c')
    resource = root.lookup(url.path)
    data = httprsc.PathProcessor(resource).extract_args(url)
    print(util.obj_to_json(data))


if __name__ == '__main__':
    test_basic_path_arg()
    test_tail_path_arg()
