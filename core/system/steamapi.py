import aiohttp
# ALLOW util.* http.*
from core.util import util
from core.http import httpabc, httpcnt, httprsc


def resources(resource: httprsc.WebResource):
    r = httprsc.ResourceBuilder(resource)
    r.psh('steamapi')
    r.put('published-file-details', _GetPublishedFileDetailsHandler())


class _GetPublishedFileDetailsHandler(httpabc.GetHandler):

    async def handle_get(self, resource, data):
        if not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        items = util.get('ids', data)
        assert items
        data, index = [], 0
        for item in items.split(','):
            data.append('&publishedfileids%5B' + str(index) + '%5D=' + item)
            index += 1
        url = 'https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/'
        data = 'itemcount=' + str(index) + ''.join(data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return await _fetch_json(url, data, headers)


async def _fetch_json(url: str, data: str, headers: dict) -> str:
    connector, timeout = aiohttp.TCPConnector(force_close=True), aiohttp.ClientTimeout(total=12.0)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        async with session.post(url, data=data, headers=headers) as response:
            assert response.status == 200
            content_type = httpcnt.HeadersTool(response).get_content_type()
            assert content_type and content_type.mime_type() == httpcnt.MIME_APPLICATION_JSON
            return await response.json()
