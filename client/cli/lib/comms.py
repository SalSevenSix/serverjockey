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
        payload = json.dumps(body) if body else None
        connection = self._init_connection()
        try:
            connection.request(util.POST, path, headers=self._headers_post, body=payload)
            return _handle_post(connection.getresponse())
        finally:
            self.close()

    def get(self, path: str, on_404: str = None) -> str | dict | list | None:
        connection = self._init_connection()
        try:
            connection.request(util.GET, path, headers=self._headers_get)
            return _handle_get(connection.getresponse(), on_404)
        finally:
            if on_404:
                self.close()

    def drain(self, url_dict: dict):
        path = '/' + '/'.join(url_dict['url'].split('/')[3:])
        connection = self._init_connection()
        try:
            draining = True
            while draining:
                connection.request(util.GET, path, headers=self._headers_get)
                draining = _handle_drain(connection.getresponse())
        finally:
            self.close()


def _handle_post(response) -> str | dict | None:
    try:
        if response.status == 204:
            return None
        if response.status == 200:
            return _to_result(response)
        raise Exception(f'HTTP POST Status: {response.status} Reason: {response.reason}')
    finally:
        response.close()


def _handle_get(response, on_404: str | None) -> str | dict | list | None:
    try:
        if response.status == 204:
            return None
        if response.status == 200:
            return _to_result(response)
        if on_404 and response.status == 404:
            return on_404
        raise Exception(f'HTTP GET Status: {response.status} Reason: {response.reason}')
    finally:
        response.close()


def _handle_drain(response) -> bool:
    try:
        if response.status == 204:
            return True
        if response.status == 200:
            for line in response.readlines():
                logging.info(util.OUT + line.decode().strip())
            return True
        if response.status == 404:
            return False
        raise Exception(f'HTTP GET Status: {response.status} Reason: {response.reason}')
    finally:
        response.close()


def _to_result(response):
    result = '\n'.join([line.decode().strip() for line in response.readlines()])
    if response.getheader('Content-Type') == 'application/json':
        return json.loads(result)
    return result
