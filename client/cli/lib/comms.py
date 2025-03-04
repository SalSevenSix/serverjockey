import logging
import json
import ssl
from http import client
# ALLOW lib.util
from . import util, cxt


class HttpConnection:

    def __init__(self, context: cxt.Context):
        url, token = context.credentials()
        self._is_https = url.startswith('https')
        self._url = url[8:] if self._is_https else url[7:]
        self._headers_get = {'X-Secret': token}
        self._headers_post = self._headers_get.copy()
        self._headers_post.update({'Content-Type': 'application/json', 'Connection': 'close'})
        self._connection = None

    def _init_connection(self):
        if not self._connection:
            if self._is_https:
                # noinspection PyProtectedMember
                self._connection = client.HTTPSConnection(self._url, context=ssl._create_unverified_context())
            else:
                self._connection = client.HTTPConnection(self._url)
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
        self._connection = None

    def post(self, path: str, body: dict = None) -> str | dict | None:
        connection, payload = self._init_connection(), json.dumps(body) if body else None
        connection.request(util.POST, path, headers=self._headers_post, body=payload)
        response = connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                result = '\n'.join([line.decode().strip() for line in response.readlines()])
                if response.getheader('Content-Type') == 'application/json':
                    return json.loads(result)
                return result
            raise Exception(f'HTTP POST Status: {response.status} Reason: {response.reason}')
        finally:
            response.close()
            self.close()

    def get(self, path: str, on_404: str = None) -> str | list | dict | None:
        connection = self._init_connection()
        connection.request(util.GET, path, headers=self._headers_get)
        response = connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                result = '\n'.join([line.decode().strip() for line in response.readlines()])
                if response.getheader('Content-Type') == 'application/json':
                    return json.loads(result)
                return result
            if on_404 and response.status == 404:
                return on_404
            raise Exception(f'HTTP GET Status: {response.status} Reason: {response.reason}')
        finally:
            response.close()  # Only closing response to allow connection reuse

    def drain(self, url_dict: dict):
        connection, path = self._init_connection(), '/' + '/'.join(url_dict['url'].split('/')[3:])
        while True:
            connection.request(util.GET, path, headers=self._headers_get)
            response = connection.getresponse()
            try:
                if response.status == 200:
                    for line in response.readlines():
                        logging.info(util.OUT + line.decode().strip())
                elif response.status == 404:
                    return
                elif response.status != 204:
                    raise Exception(f'HTTP GET Status: {response.status} Reason: {response.reason}')
            finally:
                response.close()
                self.close()
