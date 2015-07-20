from nose.tools import istest, assert_equal

from mammoth.docx.files import Files
from ..testing import test_path


@istest
def can_open_files_with_file_uri():
    path = test_path("tiny-picture.png")
    files = Files(None)
    with files.open("file:///" + path) as image_file:
        contents = image_file.read()
        assert_equal(bytes, type(contents))
        with open(path, "rb") as source_file:
            assert_equal(source_file.read(), contents)


@istest
def can_open_files_with_relative_uri():
    files = Files(test_path(""))
    with files.open("tiny-picture.png") as image_file:
        contents = image_file.read()
        assert_equal(bytes, type(contents))
        with open(test_path("tiny-picture.png"), "rb") as source_file:
            assert_equal(source_file.read(), contents)
