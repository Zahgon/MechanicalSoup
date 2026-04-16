import io
import os
import tempfile
import urllib
import weakref
import webbrowser

import bs4
import bs4.dammit
import requests

from .__version__ import __title__, __version__
from .form import Form
from .utils import LinkNotFoundError, is_multipart_file_upload


class Browser:
    """Builds a low-level Browser.

    It is recommended to use :class:`StatefulBrowser` for most applications,
    since it offers more advanced features and conveniences than Browser.

    :param session: Attach a pre-existing requests Session instead of
        constructing a new one.
    :param soup_config: Configuration passed to BeautifulSoup to affect
        the way HTML is parsed. Defaults to ``{'features': 'lxml'}``.
        If overridden, it is highly recommended to `specify a parser
        <https://www.crummy.com/software/BeautifulSoup/bs4/doc/#specifying-the-parser-to-use>`__.
        Otherwise, BeautifulSoup will issue a warning and pick one for
        you, but the parser it chooses may be different on different
        machines.
    :param requests_adapters: Configuration passed to requests, to affect
        the way HTTP requests are performed.
    :param raise_on_404: If True, raise :class:`LinkNotFoundError`
        when visiting a page triggers a 404 Not Found error.
    :param user_agent: Set the user agent header to this value.

    """
    def __init__(self, session=None, soup_config={'features': 'lxml'},
                 requests_adapters=None,
                 raise_on_404=False, user_agent=None):

        self.raise_on_404 = raise_on_404
        self.session = session or requests.Session()

        self._finalize = weakref.finalize(self.session, self.close)

        self.set_user_agent(user_agent)

        if requests_adapters is not None:
            for adaptee, adapter in requests_adapters.items():
                self.session.mount(adaptee, adapter)

        self.soup_config = soup_config or dict()

    @staticmethod
    def __looks_like_html(response):
        """Guesses entity type when Content-Type header is missing.
        Since Content-Type is not strictly required, some servers leave it out.
        """
        text = response.text.lstrip().lower()
        return text.startswith('<html') or text.startswith('<!doctype')

    @staticmethod
    def add_soup(response, soup_config):
        """Attaches a soup object to a requests response."""
        if ("text/html" in response.headers.get("Content-Type", "") or
                Browser.__looks_like_html(response)):
            # Note: By default (no charset provided in HTTP headers), requests
            # returns 'ISO-8859-1' which is the default for HTML4, even if HTML
            # code specifies a different encoding. In this case, we want to
            # resort to bs4 sniffing, hence the special handling here.
            http_encoding = (
                response.encoding
                if 'charset' in response.headers.get("Content-Type", "")
                else None
            )
            html_encoding = bs4.dammit.EncodingDetector.find_declared_encoding(
                response.content,
                is_html=True
            )
            # See https://www.w3.org/International/questions/qa-html-encoding-declarations.en#httphead  # noqa: E501
            # > The HTTP header has a higher precedence than the in-document
            # > meta declarations.
            encoding = http_encoding if http_encoding else html_encoding
            response.soup = bs4.BeautifulSoup(
                response.content,
                from_encoding=encoding,
                **soup_config
            )
        else:
            response.soup = None

    def set_cookiejar(self, cookiejar):
        """Replaces the current cookiejar in the requests session. Since the
        session handles cookies automatically without calling this function,
        only use this when default cookie handling is insufficient.

        :param cookiejar: Any `http.cookiejar.CookieJar
          <https://docs.python.org/3/library/http.cookiejar.html#http.cookiejar.CookieJar>`__
          compatible object.
        """
        pass

    def get_cookiejar(self):
        """Gets the cookiejar from the requests session."""
        pass

    def set_user_agent(self, user_agent):
        """Replaces the current user agent in the requests session headers."""
        pass

    def request(self, *args, **kwargs):
        """Straightforward wrapper around `requests.Session.request
        <http://docs.python-requests.org/en/master/api/#requests.Session.request>`__.

        :return: `requests.Response
            <http://docs.python-requests.org/en/master/api/#requests.Response>`__
            object with a *soup*-attribute added by :func:`add_soup`.

        This is a low-level function that should not be called for
        basic usage (use :func:`get` or :func:`post` instead). Use it if you
        need an HTTP verb that MechanicalSoup doesn't manage (e.g. MKCOL) for
        example.
        """
        pass

    def get(self, *args, **kwargs):
        """Straightforward wrapper around `requests.Session.get
        <http://docs.python-requests.org/en/master/api/#requests.Session.get>`__.

        :return: `requests.Response
            <http://docs.python-requests.org/en/master/api/#requests.Response>`__
            object with a *soup*-attribute added by :func:`add_soup`.
        """
        response = self.session.get(*args, **kwargs)
        if self.raise_on_404 and response.status_code == 404:
            raise LinkNotFoundError()
        Browser.add_soup(response, self.soup_config)
        return response

    def post(self, *args, **kwargs):
        """Straightforward wrapper around `requests.Session.post
        <http://docs.python-requests.org/en/master/api/#requests.Session.post>`__.

        :return: `requests.Response
            <http://docs.python-requests.org/en/master/api/#requests.Response>`__
            object with a *soup*-attribute added by :func:`add_soup`.
        """
        pass

    def put(self, *args, **kwargs):
        """Straightforward wrapper around `requests.Session.put
        <http://docs.python-requests.org/en/master/api/#requests.Session.put>`__.

        :return: `requests.Response
            <http://docs.python-requests.org/en/master/api/#requests.Response>`__
            object with a *soup*-attribute added by :func:`add_soup`.
        """
        pass

    @staticmethod
    def _get_request_kwargs(method, url, **kwargs):
        """This method exists to raise a TypeError when a method or url is
        specified in the kwargs.
        """
        pass

    @classmethod
    def get_request_kwargs(cls, form, url=None, **kwargs):
        """Extract input data from the form."""
        pass

    def _request(self, form, url=None, **kwargs):
        """Extract input data from the form to pass to a Requests session."""
        pass

    def submit(self, form, url=None, **kwargs):
        """Prepares and sends a form request.

        NOTE: To submit a form with a :class:`StatefulBrowser` instance, it is
        recommended to use :func:`StatefulBrowser.submit_selected` instead of
        this method so that the browser state is correctly updated.

        :param form: The filled-out form.
        :param url: URL of the page the form is on. If the form action is a
            relative path, then this must be specified.
        :param \\*\\*kwargs: Arguments forwarded to `requests.Session.request
            <http://docs.python-requests.org/en/master/api/#requests.Session.request>`__.
            If `files`, `params` (with GET), or `data` (with POST) are
            specified, they will be appended to by the contents of `form`.

        :return: `requests.Response
            <http://docs.python-requests.org/en/master/api/#requests.Response>`__
            object with a *soup*-attribute added by :func:`add_soup`.
        """
        pass

    def launch_browser(self, soup):
        """Launch a browser to display a page, for debugging purposes.

        :param: soup: Page contents to display, supplied as a bs4 soup object.
        """
        pass

    def close(self):
        """Close the current session, if still open."""
        pass

    def __del__(self):
        self._finalize()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
