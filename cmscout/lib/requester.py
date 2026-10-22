#! /usr/bin/env python3
import urllib.request, urllib.parse, urllib.error, ssl, http.client, http.cookiejar

# Import Objects 
from .initialize import initializer


def sanitize_url(url):
    """Quote characters http.client rejects (spaces, control chars).

    Probe targets are built from wordlists and scraped HTML, and either
    can carry characters that make http.client raise InvalidURL and kill
    the requesting thread (issues #19/#22/#25/#26). Quoting keeps the
    probe harmless; "%" stays untouched to avoid double-encoding.
    """
    return urllib.parse.quote(url, safe="/:?#[]@!$&'()*+,;=%")


class Requester:
    def __init__(self):
        self.htmltext = None
        self.status_code = None
        self.response = None
        self.headers = initializer.headers
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.cookieJar = http.cookiejar.CookieJar()
        self.cookieHandler = urllib.request.HTTPCookieProcessor(self.cookieJar)

    def _fail(self):
        # Transport failure: neutral state so callers skip this probe
        # instead of crashing on stale or None state.
        self.response = None
        self.htmltext = ""
        self.status_code = None

    def request(self, url, data):
        self.url = sanitize_url(url)
        self.data = data
        if type(data) is dict:
            data = urllib.parse.urlencode(data)
        if data : data = data.encode('utf-8')
        self.req = urllib.request.Request(url=self.url, data=data, headers=self.headers)
        urllib.request.install_opener(urllib.request.build_opener())
        try:
            # Returns 200
            if initializer.nosslcheck :
                self.response = urllib.request.urlopen(self.req, context=self.ctx)
            else:
                self.response = urllib.request.urlopen(self.req)
            # it will ignore any bad character without replacing it
            self.htmltext = self.response.read().decode('utf-8', 'ignore')
            self.status_code = 200
        except urllib.request.HTTPError as e:
            # Does not return  200
            self.response = e
            self.htmltext = e.read().decode('utf-8', 'ignore')
            self.status_code = e.code
        except (urllib.error.URLError, http.client.HTTPException, OSError):
            # Dead host, refused connection, malformed reply: skip probe.
            self._fail()

    def noredirect(self, url, data):
        self.url = sanitize_url(url)
        self.data = data
        if type(data) is dict:
            data = urllib.parse.urlencode(data)
        if data : data = data.encode('utf-8')
        self.req = urllib.request.Request(url=self.url, data=data, headers=self.headers)
        urllib.request.install_opener(urllib.request.build_opener(NoRedirects()))
        try:
            # Returns 200
            if initializer.nosslcheck :
                self.response = urllib.request.urlopen(self.req, context=self.ctx)
            else:
                self.response = urllib.request.urlopen(self.req)
            self.htmltext = self.response.read().decode('utf-8', 'ignore')
            self.status_code = 200
        except urllib.request.HTTPError as e:
            # Does not return  200
            self.response = e
            self.htmltext = e.read().decode('utf-8', 'ignore')
            self.status_code = e.code
        except (urllib.error.URLError, http.client.HTTPException, OSError):
            # Dead host, refused connection, malformed reply: skip probe.
            self._fail()

    def requestcookie(self, url, data):
        self.url = sanitize_url(url)
        self.data = data
        if type(data) is dict:
            data = urllib.parse.urlencode(data)
        if data : data = data.encode('utf-8')
        self.req = urllib.request.Request(url=self.url, data=data, headers=self.headers)
        urllib.request.install_opener(urllib.request.build_opener(self.cookieHandler))
        try:
            # Returns 200
            if initializer.nosslcheck :
                self.response = urllib.request.urlopen(self.req, context=self.ctx)
            else:
                self.response = urllib.request.urlopen(self.req)
            # it will ignore any bad character without replacing it
            self.htmltext = self.response.read().decode('utf-8', 'ignore')
            self.status_code = 200
        except urllib.request.HTTPError as e:
            # Does not return  200
            self.response = e
            self.htmltext = e.read().decode('utf-8', 'ignore')
            self.status_code = e.code
        except (urllib.error.URLError, http.client.HTTPException, OSError):
            # Dead host, refused connection, malformed reply: skip probe.
            self._fail()

class NoRedirects(urllib.request.HTTPRedirectHandler):
    # Redirect handler that simply raises a Redirect() for all http_error_30*() methods
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        RedirError = urllib.request.HTTPError(req.get_full_url(), code, msg, headers, fp)
        RedirError.status = code
        raise RedirError

requester = Requester()
