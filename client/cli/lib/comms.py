import logging
import json
from http import client
# ALLOW lib.util

_GET, _POST = 'GET', 'POST'


class HttpConnection:

    def __init__(self, config: dict):
        url, self._out, self._headers = config['url'], config['out'], {'X-Secret': config['token']}
        if url.startswith('https'):
            self._connection = client.HTTPSConnection(url[8:])
        else:
            self._connection = client.HTTPConnection(url[7:])

    def get(self, path: str) -> str | list | dict | None:
        self._connection.request(_GET, path, headers=self._headers)
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
        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})
        payload = json.dumps(body) if body else None
        self._connection.request(_POST, path, headers=headers, body=payload)
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
            self._connection.request(_GET, path, headers=self._headers)
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
