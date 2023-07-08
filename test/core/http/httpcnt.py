from core.http import httpcnt


def test():
    test_content_type_lookup()


def test_content_type_lookup():
    assert not httpcnt.ContentTypeImpl.lookup('file').is_text_type()
    assert not httpcnt.ContentTypeImpl.lookup('/path/file').is_text_type()
    assert not httpcnt.ContentTypeImpl.lookup('text').is_text_type()
    assert not httpcnt.ContentTypeImpl.lookup('/path/text').is_text_type()
    assert not httpcnt.ContentTypeImpl.lookup('/path/file.gif').is_text_type()
    assert not httpcnt.ContentTypeImpl.lookup('/path/file.gif.png').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.gif.log').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.text').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.LOG').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.1').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.123_234-123').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.___').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.---').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.prev').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.Prev').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.previous').is_text_type()
    assert httpcnt.ContentTypeImpl.lookup('/path/file.log.backup').is_text_type()
    assert not httpcnt.ContentTypeImpl.lookup('/path/file.log.gif').is_text_type()
    assert not httpcnt.ContentTypeImpl.lookup('/path/file.log.1.2').is_text_type()


if __name__ == '__main__':
    test()
