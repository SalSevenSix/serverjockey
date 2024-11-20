import unittest
from core.util import util
from core.msg import msgsvc, msgext, msgftr


class TestCoreMsg(unittest.IsolatedAsyncioTestCase):

    async def test_task_mailer(self):
        catcher = msgext.MultiCatcher(msgftr.AcceptAll(), msgftr.IsStop())
        mailer = msgsvc.TaskMailer(catcher)
        mailer.start()
        mailer.post('source', 'test-message', 'payload')
        await mailer.stop()
        message = util.single(await catcher.get())
        self.assertEqual('source', message.source())
        self.assertEqual('test-message', message.name())
        self.assertEqual('payload', message.data())

    async def test_task_multicast_mailer(self):
        mailer = msgsvc.TaskMulticastMailer()
        mailer.start()
        c1, c2 = msgext.SingleCatcher(msgftr.AcceptAll()), msgext.SingleCatcher(msgftr.AcceptAll())
        mailer.register(c1)
        mailer.register(c2)
        mailer.post('test-message', 'mot')
        self.assertIsNotNone(await c1.get())
        self.assertIsNotNone(await c2.get())
        await mailer.stop()

    async def test_single_catcher(self):
        mailer = msgsvc.TaskMulticastMailer()
        mailer.start()
        catcher = msgext.SingleCatcher(msgftr.NameEquals('mot'))
        mailer.register(catcher)
        mailer.post('test-message', 'mot')
        message = await catcher.get()
        self.assertEqual(message.source(), 'test-message')
        self.assertEqual(message.name(), 'mot')
        await mailer.stop()
