from nose.tools import istest, assert_equal

from mammoth import documents
from mammoth.docx.xmlparser import element as xml_element, text as xml_text
from mammoth.docx.document_xml import read_document_xml_element
from mammoth.docx import body_xml


@istest
class ReadXmlElementTests(object):
    @istest
    def can_read_text_within_document(self):
        element = _document_element_with_text("Hello!")
        assert_equal(
            documents.document([documents.paragraph([documents.run([documents.Text("Hello!")])])]),
            _read_and_get_document_xml_element(element)
        )
        
    @istest
    def footnotes_of_document_are_read(self):
        notes = [documents.note("footnote", "4", [documents.paragraph([])])]
        
        body_xml = xml_element("w:body")
        document_xml = xml_element("w:document", {}, [body_xml])
        
        document = _read_and_get_document_xml_element(document_xml, notes=notes)
        footnote = document.notes.find_note("footnote", "4")
        assert_equal("4", footnote.note_id)
        assert isinstance(footnote.body[0], documents.Paragraph)
    

def _read_and_get_document_xml_element(*args, **kwargs):
    body_reader = body_xml.reader()
    result = read_document_xml_element(*args, body_reader=body_reader, **kwargs)
    assert_equal([], result.messages)
    return result.value


def _document_element_with_text(text):
    return xml_element("w:document", {}, [
        xml_element("w:body", {}, [_paragraph_element_with_text(text)])
    ])

def _paragraph_element_with_text(text):
    return xml_element("w:p", {}, [_run_element_with_text(text)])

def _run_element_with_text(text):
    return xml_element("w:r", {}, [_text_element(text)])


def _text_element(value):
    return xml_element("w:t", {}, [xml_text(value)])
