from nose.tools import istest, assert_equal

from mammoth import documents
from mammoth.docx.xmlparser import element as xml_element
from mammoth.docx.comments_xml import create_comments_reader
from mammoth.docx import body_xml


@istest
def id_and_body_of_comment_is_read():
    body = [xml_element("w:p")]
    comments = create_comments_reader(body_xml.reader())(xml_element("w:comments", {}, [
        xml_element("w:comment", {"w:id": "1"}, body),
    ]))
    assert_equal(1, len(comments.value))
    assert_equal(comments.value[0].body, [documents.paragraph(children=[])])
    assert_equal("1", comments.value[0].comment_id)


@istest
def when_optional_attributes_of_comment_are_missing_then_they_are_read_as_none():
    comments = create_comments_reader(body_xml.reader())(xml_element("w:comments", {}, [
        xml_element("w:comment", {"w:id": "1"}, []),
    ]))
    comment, = comments.value
    assert_equal(None, comment.author_name)
    assert_equal(None, comment.author_initials)


@istest
def when_optional_attributes_of_comment_are_blank_then_they_are_read_as_none():
    comments = create_comments_reader(body_xml.reader())(xml_element("w:comments", {}, [
        xml_element("w:comment", {"w:id": "1", "w:author": " ", "w:initials": " "}, []),
    ]))
    comment, = comments.value
    assert_equal(None, comment.author_name)
    assert_equal(None, comment.author_initials)


@istest
def when_optional_attributes_of_comment_are_not_blank_then_they_are_read():
    comments = create_comments_reader(body_xml.reader())(xml_element("w:comments", {}, [
        xml_element("w:comment", {"w:id": "1", "w:author": "The Piemaker", "w:initials": "TP"}, []),
    ]))
    comment, = comments.value
    assert_equal("The Piemaker", comment.author_name)
    assert_equal("TP", comment.author_initials)
