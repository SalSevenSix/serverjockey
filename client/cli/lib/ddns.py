import logging
import json
import sys
import socket
import errno
from http import client
# ALLOW lib.util
from . import util


def update_duck(provider, token, domain):
    assert provider == 'duck'
    if not token or not domain:
        raise Exception('token and domain required')
    ipv4, ipv6 = _get_public_ips()
    host, path = 'www.duckdns.org', '/update?domains=' + domain + '&token=' + token
    if ipv4:
        path += '&ip=' + ipv4
    if ipv6:
        path += '&ipv6=' + ipv6
    if _http_request(host, path, timeout=20.0) != 'OK':
        raise Exception(host + ' response not OK')


# https://porkbun.com/api/json/v3/documentation
def update_pork(provider, apikey, secretapikey, domain):
    assert provider == 'pork'
    if not apikey or not secretapikey or not domain:
        raise Exception('apikey, secretapikey and domain required')
    ipv4, ipv6 = _get_public_ips()
    host, path = 'api.porkbun.com', '/api/json/v3/dns/retrieve/' + domain
    credentials = {'secretapikey': secretapikey, 'apikey': apikey}
    records = json.loads(_http_request(host, path, credentials, timeout=12.0))
    assert records.get('status') == 'SUCCESS'
    for record in records['records']:
        for record_type, content in (('A', ipv4), ('AAAA', ipv6)):
            if content and record['type'] == record_type and record['content'] != content:
                name, path = record['name'], '/api/json/v3/dns/edit/' + domain + '/' + record['id']
                body = credentials.copy()
                body['type'], body['content'] = record_type, content
                if name != domain:
                    body['name'] = name[0:len(name) - len(domain) - 1]
                logging.info('updating ' + record_type + ' for ' + name + ' to ' + content)
                body = _http_request(host, path, body, timeout=12.0)
                body = json.loads(body) if body else None
                if not body or body.get('status') != 'SUCCESS':
                    raise Exception(host + ' error response: ' + str(body))


def _get_public_ips() -> tuple:
    ipv4, ipv6 = util.get_local_ips()
    ipv6 = ipv6[0] if len(ipv6) > 0 else None
    ipv4 = _get_public_ipv4()
    return ipv4, ipv6


def _get_public_ipv4() -> str | None:
    for host, path in (('api.ipify.org', ''), ('ipv4.seeip.org', ''), ('ipinfo.io', '/ip')):
        try:
            result = _http_request(host, path, ipv4=True)
            if result:
                logging.info('sourced ' + result + ' from ' + host)
                return result
        except Exception as e:
            logging.warning('failed sourcing IPv4 from ' + host + ' : ' + str(e))
    return None


def _http_request(host: str, path: str, request_body: dict = None,
                  timeout: float = 4.0, ipv4: bool = False) -> str | None:
    body = json.dumps(request_body) if request_body else None
    method = util.POST if body else util.GET
    headers = {'Connection': 'close'}
    if body:
        headers.update({'Content-Type': 'application/json', 'Content-Length': str(len(body))})
    connection = _HTTPSConnection(host, timeout=timeout) if ipv4 else client.HTTPSConnection(host, timeout=timeout)
    response = None
    try:
        logging.info(method + ' https://' + host + path)
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        if response.status == 204:
            return None
        if response.status == 200:
            response_body = response.read()
            return response_body.decode().strip() if response_body else ''
        raise Exception(f'HTTP {method} Status: {response.status} Reason: {response.reason}')
    finally:
        if response:
            response.close()
        connection.close()


class _HTTPSConnection(client.HTTPSConnection):
    # noinspection All
    def connect(self):
        sys.audit("http.client.connect", self, self.host, self.port)
        # self.sock = socket.create_connection((self.host, self.port), self.timeout, self.source_address)
        self.sock = socket.socket(socket.AF_INET)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError as e:
            if e.errno != errno.ENOPROTOOPT:
                raise
        # logging.info('Socket {} {} {}'.format(self.host, self.port, self.timeout))
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)
