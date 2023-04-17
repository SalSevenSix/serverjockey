from core.util import aggtrf
from core.msg import msgftr, msglog
from core.http import httpsubs


def archive_selector():
    return httpsubs.Selector(
        msg_filter=msglog.LoggingPublisher.FILTER_ALL_LEVELS,
        completed_filter=msgftr.DataEquals('END Archive Directory'),
        aggregator=aggtrf.StrJoin('\n'))


def unpacker_selector():
    return httpsubs.Selector(
        msg_filter=msglog.LoggingPublisher.FILTER_ALL_LEVELS,
        completed_filter=msgftr.DataEquals('END Unpack Directory'),
        aggregator=aggtrf.StrJoin('\n'))
