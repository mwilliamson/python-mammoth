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

