from nose.tools import istest, assert_equal

from mammoth.docx.files import Files, InvalidFileReferenceError
from ..testing import test_path, assert_raises


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


@istest
def given_base_is_not_set_when_opening_relative_uri_then_error_is_raised():
    files = Files(None)
    error = assert_raises(InvalidFileReferenceError, lambda: files.open("not-a-real-file.png"))
    expected_message = (
        "could not find external image 'not-a-real-file.png', fileobj has no name"
    )
    assert_equal(expected_message, str(error))


@istest
def error_is_raised_if_relative_uri_cannot_be_opened():
    files = Files("/tmp")
    error = assert_raises(InvalidFileReferenceError, lambda: files.open("not-a-real-file.png"))
    expected_message = (
        "could not open external image: 'not-a-real-file.png' (document directory: '/tmp')\n" +
        "[Errno 2] No such file or directory: '/tmp/not-a-real-file.png'"
    )
    assert_equal(expected_message, str(error))


@istest
def error_is_raised_if_file_uri_cannot_be_opened():
    files = Files("/tmp")
    error = assert_raises(InvalidFileReferenceError, lambda: files.open("file:///not-a-real-file.png"))
    expected_message = "could not open external image: 'file:///not-a-real-file.png' (document directory: '/tmp')\n"
    assert str(error).startswith(expected_message)
