from core.msg import msgabc
from core.http import httpabc
from core.system import svrext


def snr(mailer: msgabc.MulticastMailer, delegate: httpabc.ABC_HANDLER) -> svrext.CheckServerNotRunningHandler:
    return svrext.CheckServerNotRunningHandler(mailer, delegate)
