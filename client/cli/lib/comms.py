import logging
import json
from http import client

GET, POST = 'GET', 'POST'


class HttpConnection:

    def __init__(self, clientfile: str):
        with open(file=clientfile, mode='r') as file:
            data = json.load(file)
        url, self._headers = data['SERVER_URL'], {'X-Secret': data['SERVER_TOKEN']}
        if url.startswith('https'):
            self._connection = client.HTTPSConnection(url[8:])
        else:
            self._connection = client.HTTPConnection(url[7:])

    def get(self, path: str) -> str | None:
        self._connection.request(GET, path, headers=self._headers)
        response = self._connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                return '/n'.join([line.decode() for line in response.readlines()])
            raise Exception('HTTP GET Status: {} Reason: {}'.format(response.status, response.reason))
        finally:
            response.close()

    def post(self, path: str, body: str = None) -> str | None:
        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})
        self._connection.request(POST, path, headers=headers, body=body)
        response = self._connection.getresponse()
        try:
            if response.status == 204:
                return None
            if response.status == 200:
                return '/n'.join([line.decode() for line in response.readlines()])
            raise Exception('HTTP POST Status: {} Reason: {}'.format(response.status, response.reason))
        finally:
            response.close()

    def drain(self, url_dict: dict):
        url = url_dict['url'].split('/')[3:]
        path = '/' + '/'.join(url)
        while True:
            self._connection.request(GET, path, headers=self._headers)
            response = self._connection.getresponse()
            try:
                if response.status == 200:
                    for line in response.readlines():
                        logging.info(line.decode().strip())
                elif response.status == 404:
                    return
                elif response.status != 204:
                    raise Exception('HTTP POST Status: {} Reason: {}'.format(response.status, response.reason))
            finally:
                response.close()

    def close(self):
        self._connection.close()
