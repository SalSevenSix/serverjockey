from core.util import aggtrf
from core.msg import msgftr, msgext, msglog
from core.http import httpsubs


def archive_selector():
    return httpsubs.Selector(
        msg_filter=msglog.LoggingPublisher.FILTER_ALL_LEVELS,
        completed_filter=msgext.Archiver.FILTER_DONE,
        aggregator=aggtrf.StrJoin('\n'))


def unpacker_selector():
    return httpsubs.Selector(
        msg_filter=msglog.LoggingPublisher.FILTER_ALL_LEVELS,
        completed_filter=msgext.Unpacker.FILTER_DONE,
        aggregator=aggtrf.StrJoin('\n'))
