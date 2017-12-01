import requests
import requests.cookies
import json
import uuid
import hashlib
from retrying import retry
import requests.cookies
import urllib3
import logging
from bs4 import BeautifulSoup
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WebScraper(object):
    pass


class NoSessionBound(Exception):
    pass


class CookieStorage(object):
    def __init__(self):
        self.session = None
        self.session_id = None
        self.data = []

    def as_cookiejar(self):
        cj = requests.cookies.RequestsCookieJar()
        for cookie in self.data:
            cj.set_cookie(requests.cookies.create_cookie(**cookie))
        return cj

    def flush(self):
        if self.session is None:
            raise NoSessionBound("CookieStorage is not bound to any session")

        self.data = []
        for cookie in self.session.cookies:
            self.data.append({
                "version": cookie.version,
                "name": cookie.name,
                "value": cookie.value,
                "port": cookie.port,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "expires": cookie.expires,
                "discard": cookie.discard,
                "comment": cookie.comment,
                "comment_url": cookie.comment_url,
                "rfc2109": cookie.rfc2109
            })
        self.save()
        return self.data

    def load(self):
        pass

    def save(self):
        pass


class FileCookieStorage(CookieStorage):
    def load(self):
        try:
            with open(self.session_id + ".json", 'r') as f:
                self.data = json.loads(f.read())
        except FileNotFoundError:
            self.data = {}

    def save(self):
        with open(self.session_id + ".json", 'w') as f:
            f.write(json.dumps(self.data))


class Browser(object):
    def __init__(self, session_id=str(uuid.uuid4()), cookies_enabled=True, cookie_storage=None):
        self.cookie_storage = None
        if cookies_enabled:
            self.browser = requests.session()
            self.browser.headers.update({"User-Agent": 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})
            if cookie_storage is not None:
                self.cookie_storage = cookie_storage
                self.cookie_storage.session_id = session_id
                self.cookie_storage.session = self.browser
                self.cookie_storage.load()

                self.browser.cookies = self.cookie_storage.as_cookiejar()
        else:
            self.browser = requests

    def __getattr__(self, attr):
        return self.browser.__getattribute__(attr)


class AuthMethod(object):
    def __init__(self, username, password, namespace):
        self.username = username
        self.password = password
        self.namespace = namespace

    def credentials_hash(self):
        return hashlib.md5(":".join([self.namespace, self.username, self.password]).encode()).hexdigest()


class UnauthenticatedException(Exception):
    pass


class InvalidCredentialsException(Exception):
    pass


class Web(object):
    def __init__(self, **kwargs):
        self.logger = logging.getLogger('scrapium')
        self.browser = Browser(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @retry(stop_max_attempt_number=3, wait_random_min=5000, wait_random_max=10000)  # 5 and 10 seconds
    def get(self, url):
        self.logger.debug("GET {url}".format(url=url))
        return self.browser.get(url, verify=False)

    @retry(stop_max_attempt_number=3, wait_random_min=5000, wait_random_max=10000)  # 5 and 10 seconds
    def post(self, url, data):
        self.logger.debug("POST {url}".format(url=url))
        return self.browser.post(url, data, verify=False)

    @staticmethod
    def html(text):
        return BeautifulSoup(text, "html.parser")

    def get_html(self, url):
        r = self.get(url)
        return self.html(r.text)

    def post_html(self, url, data):
        r = self.post(url, data)
        return self.html(r.text)


class AuthenticatedWeb(Web):
    def __init__(self, auth_method, cookie_storage=CookieStorage()):
        self.auth_method = auth_method
        self.id = auth_method.credentials_hash()
        super().__init__(cookie_storage=cookie_storage, session_id=self.id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()

    def flush(self):
        self.browser.cookie_storage.flush()

    def is_logged(self, request):
        return False

    def login(self):
        raise InvalidCredentialsException("Invalid credentials")

    def _check_login(self, request):
        if self.is_logged(request):
            return request
        else:
            self.logger.debug("Not logged in, logging in and retrying")
            self.login()
            raise UnauthenticatedException("User is not logged in")

    @retry(stop_max_attempt_number=3, wait_random_min=5000, wait_random_max=10000)  # 5 and 10 seconds
    def get(self, url):
        r = super().get(url)
        return self._check_login(r)

    @retry(stop_max_attempt_number=3, wait_random_min=5000, wait_random_max=10000)  # 5 and 10 seconds
    def post(self, url, data):
        r = super().post(url, data)
        return self._check_login(r)


