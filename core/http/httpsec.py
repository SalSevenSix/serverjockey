import time
import base64
# ALLOW util.* msg*.* context.* http.httpabc, http.httpcnt
from core.util import gc, util
from core.http import httpabc, httpcnt

_SECURE = '_SECURE'
_COOKIE_NAME = 'secret'


def make_secure(data: httpabc.ABC_DATA_GET, secure: bool):
    if _SECURE in data:
        del data[_SECURE]
    if secure:
        data[_SECURE] = True


def is_secure(data: httpabc.ABC_DATA_GET) -> bool:
    return util.get(_SECURE, data, False) is True


class LoginResponse:

    def __init__(self):
        pass


class SecurityService:
    COUNT, TIMOUT = 10, 5.0

    def __init__(self, secret: str):
        self._secret = secret
        self._failures = _SecurityFailures()

    def set_cookie(self, response):
        response.set_cookie(_COOKIE_NAME, self._secret, max_age=86400, httponly=True, samesite='Lax')

    def check(self, request) -> bool:
        now, remote = time.time(), request.remote
        count, last = self._failures.get(remote)
        if count >= SecurityService.COUNT:
            if (now - last) < SecurityService.TIMOUT:
                self._failures.set(remote, now)
                raise httpabc.ResponseBody.UNAUTHORISED
            self._failures.remove(remote)
        secret = SecurityService._get_secret(request)
        if secret is None:
            return False  # No token provided, which is acceptable for public requests
        if secret == self._secret:
            return True  # Correct token provided
        # Incorrect token...
        self._failures.add(remote, now)
        raise httpabc.ResponseBody.UNAUTHORISED

    @staticmethod
    def _get_secret(request) -> str | None:
        headers = httpcnt.HeadersTool(request)
        secret = headers.get(httpcnt.X_SECRET)
        if secret is None:
            secret = SecurityService._extract_secret(headers.get(httpcnt.AUTHORIZATION))
        if secret is None:
            secret = request.cookies.get(_COOKIE_NAME)
        return secret

    @staticmethod
    def _extract_secret(authorization: str | None) -> str | None:
        if not authorization or not authorization.lower().startswith('basic'):
            return None
        credentials = authorization[5:].strip()
        credentials = base64.b64decode(credentials)
        credentials = str(credentials, gc.UTF_8)
        if not credentials or not credentials.startswith('admin:'):
            return None
        return credentials[6:]


class _SecurityFailures:

    def __init__(self):
        self._failures = {}

    def get(self, remote) -> tuple:
        failure = util.get(remote, self._failures)
        return failure if failure else (0, None)

    def set(self, remote, now: float):
        count = self.get(remote)[0]
        self._failures[remote] = (count, now)

    def add(self, remote, now: float):
        self._clear(now)
        count = self.get(remote)[0]
        self._failures[remote] = (count + 1, now)

    def remove(self, remote):
        if remote in self._failures:
            del self._failures[remote]

    def _clear(self, now: float):
        remotes = []
        for remote, failure in self._failures.items():
            if (now - failure[1]) >= SecurityService.TIMOUT:
                remotes.append(remote)
        for remote in remotes:
            self.remove(remote)
