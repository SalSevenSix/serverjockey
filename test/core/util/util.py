from core.util import util


def test_base64_coding():
    value = 'So?<p> $ – _ . + ! * ‘ ( ) , [ ] { } | \\ " % ~ # < >'
    encoded = util.urlsafe_b64encode(value)
    assert encoded.count('+') == 0
    assert encoded.count('/') == 0
    assert value == util.urlsafe_b64decode(encoded)


if __name__ == '__main__':
    test_base64_coding()
