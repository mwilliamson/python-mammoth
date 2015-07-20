import os
import contextlib
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Files(object):
    def __init__(self, base):
        self._base = base
    
    def open(self, uri):
        if _is_absolute(uri):
            return contextlib.closing(urlopen(uri))
        else:
            return open(os.path.join(self._base, uri), "rb")


def _is_absolute(url):
    return urlparse(url).scheme != ""
