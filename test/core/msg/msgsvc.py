import unittest
import asyncio
from core.msg import msgsvc, msgext, msgftr, msglog


async def send_test_messages(mailer):
    mailer.post('test-message', 'mot')
    mailer.post('test-message', 'hai')
    mailer.post('test-message', 'ba')
    mailer.post('test-message', 'bon')
    mailer.post('test-message', 'nam')
    mailer.post('test-message', 'sau')


class TestCoreUtil(unittest.IsolatedAsyncioTestCase):

    async def test_mailer(self):
        subscriber = msglog.PrintSubscriber()
        mailer = msgsvc.TaskMailer(subscriber)
        mailer.start()
        test_messages = asyncio.create_task(send_test_messages(mailer))
        await test_messages
        await mailer.stop()

    async def test_multicastmailer(self):
        mailer = msgsvc.TaskMulticastMailer()
        mailer.start()
        mailer.register(msglog.PrintSubscriber())
        mailer.register(msglog.PrintSubscriber())
        test_messages = asyncio.create_task(send_test_messages(mailer))
        await test_messages
        await mailer.stop()

    async def test_catching(self):
        mailer = msgsvc.TaskMulticastMailer()
        mailer.start()
        mailer.register(msglog.PrintSubscriber())
        catcher = msgext.SingleCatcher(msgftr.NameEquals('bon'))
        mailer.register(catcher)
        test_messages = asyncio.create_task(send_test_messages(mailer))
        message = await catcher.get()
        await test_messages
        self.assertEqual(message.name(), 'bon')
        await mailer.stop()
