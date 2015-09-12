import contextlib

from zipfile import ZipFile


def open_zip(fileobj, mode):
    return _Zip(ZipFile(fileobj, mode))


class _Zip(object):
    def __init__(self, zip_file):
        self._zip_file = zip_file
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self._zip_file.close()

    def open(self, name):
        return contextlib.closing(self._zip_file.open(name))

    def exists(self, name):
        try:
            self._zip_file.getinfo(name)
            return True
        except KeyError:
            return False

    def write_str(self, name, value):
        self._zip_file.writestr(name, value)
    
    def read_str(self, name):
        return self._zip_file.read(name).decode("utf8")
