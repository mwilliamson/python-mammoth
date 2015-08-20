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
    
    def verify(self, uri):
        with self.open(uri):
            pass
    
    def open(self, uri):
        if _is_absolute(uri):
            return contextlib.closing(urlopen(uri))
        elif self._base is not None:
            return open(os.path.join(self._base, uri), "rb")
        else:
            raise InvalidFileReferenceError("could not find external image '{0}', fileobj has no name".format(uri))


def _is_absolute(url):
    return urlparse(url).scheme != ""


class InvalidFileReferenceError(ValueError):
    pass
