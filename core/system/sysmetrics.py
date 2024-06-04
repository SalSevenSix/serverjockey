from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
# ALLOW util.* msg*.* context.* http.*
from core.util import funcutil
from core.http import httpabc, httpcnt, httpsec

_CONTENT_TYPE_LATEST = httpcnt.ContentTypeImpl(CONTENT_TYPE_LATEST)
_generate_latest = funcutil.to_async(generate_latest)


class SystemMetricsHandler(httpabc.GetHandler):

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        body = await _generate_latest()
        return httpabc.ResponseBody(body, _CONTENT_TYPE_LATEST)
