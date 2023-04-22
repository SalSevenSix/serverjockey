import asyncio
from core.msg import msgsvc, msgext, msgftr, msglog


def test():
    asyncio.run(test_mailer())
    asyncio.run(test_multicastmailer())
    asyncio.run(test_catching())


async def send_test_messages(mailer):
    mailer.post('test-message', 'mot')
    mailer.post('test-message', 'hai')
    mailer.post('test-message', 'ba')
    mailer.post('test-message', 'bon')
    mailer.post('test-message', 'nam')
    mailer.post('test-message', 'sau')


async def test_mailer():
    subscriber = msglog.PrintSubscriber()
    mailer = msgsvc.TaskMailer(subscriber)
    mailer.start()
    test_messages = asyncio.create_task(send_test_messages(mailer))
    await test_messages
    await mailer.stop()


async def test_multicastmailer():
    mailer = msgsvc.TaskMulticastMailer()
    mailer.start()
    mailer.register(msglog.PrintSubscriber())
    mailer.register(msglog.PrintSubscriber())
    test_messages = asyncio.create_task(send_test_messages(mailer))
    await test_messages
    await mailer.stop()


async def test_catching():
    mailer = msgsvc.TaskMulticastMailer()
    mailer.start()
    mailer.register(msglog.PrintSubscriber())
    catcher = msgext.SingleCatcher(msgftr.NameEquals('bon'))
    mailer.register(catcher)
    test_messages = asyncio.create_task(send_test_messages(mailer))
    message = await catcher.get()
    await test_messages
    assert message.name() == 'bon'
    await mailer.stop()


if __name__ == '__main__':
    test()
