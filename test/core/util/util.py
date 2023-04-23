from core.util import util


def test():
    test_base64_coding()
    test_script_escape()
    test_build_url()
    test_left_chop_and_strip()
    test_right_chop_and_strip()


def test_base64_coding():
    value = 'So?<p> $ – _ . + ! * ‘ ( ) , [ ] { } | \\ " % ~ # < >'
    encoded = util.urlsafe_b64encode(value)
    assert encoded.count('+') == 0
    assert encoded.count('/') == 0
    assert value == util.urlsafe_b64decode(encoded)


def test_script_escape():
    assert 'iwbums build14' == util.script_escape('iwbums build14')
    assert '1.8.3' == util.script_escape('1.8.3')
    assert '\#\$\*\&' == util.script_escape('#$*&')


def test_build_url():
    assert 'http://foo.bar' == util.build_url(host='foo.bar')
    assert 'http://foo.bar/' == util.build_url(host='foo.bar', path='/')
    assert 'http://foo.bar/aaa/bbb' == util.build_url(host='foo.bar', path='aaa/bbb')
    assert 'http://foo.bar/aaa/bbb' == util.build_url(host='foo.bar', path='/aaa/bbb')
    assert 'http://foo.bar/aaa/bbb' == util.build_url(host='foo.bar', port=80, path='/aaa/bbb')
    assert 'http://foo.bar:6164/aaa/bbb' == util.build_url(host='foo.bar', port=6164, path='/aaa/bbb')
    assert 'https://foo.bar:6164/aaa/bbb' == util.build_url(scheme='https', host='foo.bar', port=6164, path='/aaa/bbb')
    assert 'http://foo.bar/a?x=y&a=b' == util.build_url(host='foo.bar', path='/a?x=y&a=b')


def test_left_chop_and_strip():
    assert '' == util.left_chop_and_strip('', '')
    assert 'hey yo }) the end bit' == util.left_chop_and_strip('Hello world ({ hey yo }) the end bit', '({')


def test_right_chop_and_strip():
    assert '' == util.right_chop_and_strip('', '')
    assert 'Hello world ({ hey yo' == util.right_chop_and_strip('Hello world ({ hey yo }) the end bit', '})')


if __name__ == '__main__':
    test()
