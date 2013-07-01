#!/usr/bin/env python
#-*- coding:utf-8 -*-
 
import sys
import logging
import urllib
 
import bs4
import requests
import requests.exceptions
 
 
class URLFactory(object):
    """A factory to generate absolute url from html attribute.
 
    It's just like a link parser of the browser.
    """
 
    def __init__(self, prefix, only_current_host=True):
        self.prefix = prefix.rstrip("/")
        self.only_current_host = only_current_host
 
    def __call__(self, url, current=None):
        url = urllib.basejoin(current or self.prefix, url)
        if self.only_current_host and not url.startswith(self.prefix):
            url = self.prefix
        url = url.rsplit("#", 1)[0].rstrip("/")  # remove the url hash
        return url
 
 
class LinkChecker(object):
    """A spider to test all link of a site."""
 
    def __init__(self, make_url=None):
        #: initialize a logger
        self.logger = logging.Logger(self.__class__.__name__)
        #: creates the request client
        self.client = requests.session()
        #: the visited urls
        self.visited = set()
        #: the url factory
        self.make_url = make_url
 
    def make_soup(self, http_method, url, **kwargs):
        """Create a beautiful soup object from a url and a requests method."""
        try:
            response = http_method(url, **kwargs)
        except requests.exceptions.InvalidSchema:
            raise SkipError
        except requests.exceptions.ConnectionError as error:
            self.logger.error(error)
            raise SkipError
 
        if response.status_code != 200:
            raise HTTPError(response.status_code)
 
        if "html" not in response.headers.get("content-type"):
            raise SkipError
 
        return bs4.BeautifulSoup(response.text)
 
    def parse_page_links(self, url):
        """Parse links from the DOM of the page."""
        urls = set([self.make_url(url)])
        while urls:
            url = urls.pop()
 
            #: avoid to visit a link repeatedly
            if url in self.visited:
                continue
 
            try:
                #: make request and create the soup object
                soup = self.make_soup(self.client.get, url)
                #: record a information log
                self.logger.info("GET %s" % url)
            except HTTPError as error:
                #: failed in the request, the url may be wrong.
                #: record a warning log
                self.logger.info("HTTP[%d] %s" % (error.status_code, url))
            except SkipError as error:
                self.logger.info("SKIP %s" % url)
            else:
                #: get all links and parse it
                urls.update(
                        self.make_url(link.attrs.get("href"), current=url)
                        for link in soup.find_all("a"))
            finally:
                #: record the visited history
                urls.discard(url)
                self.visited.add(url)
 
    def start(self):
        """Start to work."""
        #: start to parse a page
        self.parse_page_links("/")
 
 
class SkipError(Exception):
    """The content type is not html or other skip reason."""
 
 
class HTTPError(Exception):
    """The HTTP error exception."""
 
    def __init__(self, status_code):
        super(HTTPError, self).__init__("A HTTP error has occured "
                "because the response status is %d" % status_code)
        self.status_code = status_code
 
 
def make_logging_handler(level=logging.DEBUG):
    """A factory to create a logging handler.
 
    It dump all log to standard error stream.
    """
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    return handler
 
 
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: %s http://example.com" % sys.argv[0]
        sys.exit(1)
    make_url = URLFactory(sys.argv[1])
    checker = LinkChecker(make_url=make_url)
    checker.logger.addHandler(make_logging_handler())
    checker.start()
