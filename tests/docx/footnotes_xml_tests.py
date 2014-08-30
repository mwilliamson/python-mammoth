from nose.tools import istest, assert_equal, assert_is

from mammoth.docx.xmlparser import element as xml_element
from mammoth.docx.footnotes_xml import read_footnotes_xml_element


@istest
def id_and_body_of_footnote_are_read():
    footnote_body = [xml_element("w:p")]
    footnotes = read_footnotes_xml_element(xml_element("w:footnotes", {}, [
        xml_element("w:footnote", {"w:id": "1"}, footnote_body),
    ]))
    assert_equal(1, len(footnotes))
    assert_is(footnote_body, footnotes[0].body)
    assert_equal("1", footnotes[0].id)


@istest
def continuation_separator_is_ignored():
    _assert_footnote_type_is_ignored("continuationSeparator")


@istest
def separator_is_ignored():
    _assert_footnote_type_is_ignored("separator")


def _assert_footnote_type_is_ignored(footnote_type):
    footnote_body = [xml_element("w:p")]
    footnotes = read_footnotes_xml_element(xml_element("w:footnotes", {}, [
        xml_element("w:footnote", {"w:id": "1", "w:type": footnote_type}, footnote_body),
    ]))
    assert_equal(0, len(footnotes))
    
