import unittest
from core.http import httpcnt


class TestCoreHttpHttpCnt(unittest.TestCase):

    def test_content_type_init_text_charset(self):
        ct = httpcnt.ContentTypeImpl('text/plain; charset=utf-8')
        self.assertEqual('text/plain; charset=utf-8', ct.content_type())
        self.assertEqual('text/plain', ct.mime_type())
        self.assertEqual('utf-8', ct.encoding())
        self.assertTrue(ct.is_text_type())

    def test_content_type_init_text_nocharset(self):
        ct = httpcnt.ContentTypeImpl('text/plain')
        self.assertEqual('text/plain', ct.content_type())
        self.assertEqual('text/plain', ct.mime_type())
        self.assertIsNone(ct.encoding())
        self.assertTrue(ct.is_text_type())

    def test_content_type_init_prometheus(self):
        ct = httpcnt.ContentTypeImpl('text/plain; version=0.0.4; charset=utf-8')
        self.assertEqual('text/plain; version=0.0.4; charset=utf-8', ct.content_type())
        self.assertEqual('text/plain', ct.mime_type())
        self.assertEqual('utf-8', ct.encoding())
        self.assertTrue(ct.is_text_type())

    def test_content_type_init_html(self):
        ct = httpcnt.ContentTypeImpl('text/html')
        self.assertEqual('text/html', ct.content_type())
        self.assertEqual('text/html', ct.mime_type())
        self.assertIsNone(ct.encoding())
        self.assertTrue(ct.is_text_type())

    def test_content_type_init_binary(self):
        ct = httpcnt.ContentTypeImpl('image/gif')
        self.assertEqual('image/gif', ct.content_type())
        self.assertEqual('image/gif', ct.mime_type())
        self.assertIsNone(ct.encoding())
        self.assertFalse(ct.is_text_type())

    def test_content_type_lookup(self):
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('file').is_text_type())
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('/path/file').is_text_type())
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('text').is_text_type())
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('/path/text').is_text_type())
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('/path/file.gif').is_text_type())
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('/path/file.gif.png').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.gif.log').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.text').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.LOG').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.1').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.123_234-123').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.___').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.---').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.prev').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.Prev').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.previous').is_text_type())
        self.assertTrue(httpcnt.ContentTypeImpl.lookup('/path/file.log.backup').is_text_type())
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('/path/file.log.gif').is_text_type())
        self.assertFalse(httpcnt.ContentTypeImpl.lookup('/path/file.log.1.2').is_text_type())
