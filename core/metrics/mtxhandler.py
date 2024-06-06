import prometheus_client
# ALLOW util.* msg*.* context.* http.*
from core.util import funcutil
from core.http import httpabc, httpcnt, httpsec
from core.metrics import mtxutil

_CONTENT_TYPE_LATEST = httpcnt.ContentTypeImpl(prometheus_client.CONTENT_TYPE_LATEST)
_generate_latest = funcutil.to_async(prometheus_client.generate_latest)


class MetricsHandler(httpabc.GetHandler):

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        body = await _generate_latest(mtxutil.REGISTRY)
        return httpabc.ResponseBody(body, _CONTENT_TYPE_LATEST)
