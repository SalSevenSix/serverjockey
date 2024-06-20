import logging
import json
import ssl
from http import client
# ALLOW lib.util
from . import util


class HttpConnection:

    def __init__(self, config: dict):
        self._headers_get = {'X-Secret': config['token']}
        self._headers_post = self._headers_get.copy()
        self._headers_post.update({'Content-Type': 'application/json', 'Connection': 'close'})
        url, self._out = config['url'], config['out']
        if url.startswith('https'):
            # noinspection PyProtectedMember
            self._connection = client.HTTPSConnection(url[8:], context=ssl._create_unverified_context())
        else:
            self._connection = client.HTTPConnection(url[7:])

    def get(self, path: str) -> str | list | dict | None:
        self._connection.request(util.GET, path, headers=self._headers_get)
        response = self._connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                result = '\n'.join([line.decode().strip() for line in response.readlines()])
                if response.getheader('Content-Type') == 'application/json':
                    return json.loads(result)
                return result
            raise Exception('HTTP GET Status: {} Reason: {}'.format(response.status, response.reason))
        finally:
            response.close()

    def post(self, path: str, body: dict = None) -> str | dict | None:
        payload = json.dumps(body) if body else None
        self._connection.request(util.POST, path, headers=self._headers_post, body=payload)
        response = self._connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                result = '\n'.join([line.decode().strip() for line in response.readlines()])
                if response.getheader('Content-Type') == 'application/json':
                    return json.loads(result)
                return result
            raise Exception('HTTP POST Status: {} Reason: {}'.format(response.status, response.reason))
        finally:
            response.close()

    def drain(self, url_dict: dict):
        path = '/' + '/'.join(url_dict['url'].split('/')[3:])
        while True:
            self._connection.request(util.GET, path, headers=self._headers_get)
            response = self._connection.getresponse()
            try:
                if response.status == 200:
                    for line in response.readlines():
                        logging.info(self._out + line.decode().strip())
                elif response.status == 404:
                    return
                elif response.status != 204:
                    raise Exception('HTTP GET Status: {} Reason: {}'.format(response.status, response.reason))
            finally:
                response.close()

    def close(self):
        self._connection.close()
