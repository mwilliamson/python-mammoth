import contextlib
import io
import shutil

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

    def read_str(self, name):
        return self._zip_file.read(name).decode("utf8")


def update_zip(fileobj, files):
    source = ZipFile(fileobj, "r")
    try:
        destination_fileobj = io.BytesIO()
        destination = ZipFile(destination_fileobj, "w")
        try:
            names = set(source.namelist()) | set(files.keys())
            for name in names:
                if name in files:
                    contents = files[name]
                else:
                    contents = source.read(name)
                destination.writestr(name, contents)
        finally:
            destination.close()
    finally:
        source.close()
    
    fileobj.seek(0)
    destination_fileobj.seek(0)
    shutil.copyfileobj(destination_fileobj, fileobj)
