import io

from nose.tools import istest, assert_equal

from mammoth.docx.style_map import write_style_map, read_style_map
from mammoth.zips import open_zip


@istest
def reading_embedded_style_map_on_document_without_embedded_style_map_returns_none():
    fileobj = _normal_docx()
    assert_equal(None, read_style_map(fileobj))


@istest
def embedded_style_map_can_be_read_after_being_written():
    fileobj = _normal_docx()
    write_style_map(fileobj, "p => h1")
    assert_equal("p => h1", read_style_map(fileobj))


@istest
def embedded_style_map_is_written_to_separate_file():
    fileobj = _normal_docx()
    write_style_map(fileobj, "p => h1")
    with open_zip(fileobj, "r") as zip_file:
        assert_equal("p => h1", zip_file.read_str("mammoth/style-map"))


def _normal_docx():
    fileobj = io.BytesIO()
    with open_zip(fileobj, "w") as zip_file:
        zip_file.write_str("placeholder", "placeholder")
    return fileobj
