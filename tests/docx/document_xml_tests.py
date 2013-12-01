from nose.tools import istest, assert_equal

from mammoth import documents
from mammoth.docx.xmlparser import element as xml_element, text as xml_text
from mammoth.docx.document_xml import read_document_xml_element
from mammoth.docx.numbering_xml import Numbering, NumberingLevel


@istest
class ReadXmlElementTests(object):
    @istest
    def text_from_text_element_is_read(self):
        element = _text_element("Hello!")
        assert_equal(documents.Text("Hello!"), read_document_xml_element(element))
    
    @istest
    def can_read_text_within_run(self):
        element = _run_element_with_text("Hello!")
        assert_equal(
            documents.run([documents.Text("Hello!")]),
            read_document_xml_element(element)
        )
    
    @istest
    def can_read_text_within_paragraph(self):
        element = _paragraph_element_with_text("Hello!")
        assert_equal(
            documents.paragraph([documents.run([documents.Text("Hello!")])]),
            read_document_xml_element(element)
        )
    
    @istest
    def can_read_text_within_document(self):
        element = _document_element_with_text("Hello!")
        assert_equal(
            documents.Document([documents.paragraph([documents.run([documents.Text("Hello!")])])]),
            read_document_xml_element(element)
        )
        
    @istest
    def paragraph_has_no_style_if_it_has_no_properties(self):
        element = xml_element("w:p")
        assert_equal(None, read_document_xml_element(element).style_name)
        
    @istest
    def paragraph_has_style_name_read_from_paragraph_properties_if_present(self):
        style_xml = xml_element("w:pStyle", {"w:val": "Heading1"})
        properties_xml = xml_element("w:pPr", {}, [style_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        paragraph = read_document_xml_element(paragraph_xml)
        assert_equal("Heading1", paragraph.style_name)
        
    @istest
    def paragraph_has_no_numbering_if_it_has_no_numbering_properties(self):
        element = xml_element("w:p")
        assert_equal(None, read_document_xml_element(element).numbering)
        
    @istest
    def paragraph_has_numbering_properties_from_paragraph_properties_if_present(self):
        numbering_properties_xml = xml_element("w:numPr", {}, [
            xml_element("w:ilvl", {"w:val": "1"}),
            xml_element("w:numId", {"w:val": "42"}),
        ])
        properties_xml = xml_element("w:pPr", {}, [numbering_properties_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        
        numbering = Numbering({"42": {"1": NumberingLevel("1", True)}})
        paragraph = read_document_xml_element(paragraph_xml, numbering=numbering)
        
        assert_equal("1", paragraph.numbering.level_index)
        assert_equal(True, paragraph.numbering.is_ordered)
    
    @istest
    def run_has_no_style_if_it_has_no_properties(self):
        element = xml_element("w:r")
        assert_equal(None, read_document_xml_element(element).style_name)
        
    @istest
    def run_has_style_name_read_from_run_properties_if_present(self):
        style_xml = xml_element("w:rStyle", {"w:val": "Emphasis"})
        run = self._read_run_with_properties([style_xml])
        assert_equal("Emphasis", run.style_name)
        
    @istest
    def run_is_not_bold_if_bold_element_is_not_present(self):
        run = self._read_run_with_properties([])
        assert_equal(False, run.is_bold)
    
    @istest
    def run_is_bold_if_bold_element_is_present(self):
        run = self._read_run_with_properties([xml_element("w:b")])
        assert_equal(True, run.is_bold)
        
    @istest
    def run_is_not_italic_if_italic_element_is_not_present(self):
        run = self._read_run_with_properties([])
        assert_equal(False, run.is_italic)
    
    @istest
    def run_is_italic_if_italic_element_is_present(self):
        run = self._read_run_with_properties([xml_element("w:i")])
        assert_equal(True, run.is_italic)
    
    def _read_run_with_properties(self, properties):
        properties_xml = xml_element("w:rPr", {}, properties)
        run_xml = xml_element("w:r", {}, [properties_xml])
        return read_document_xml_element(run_xml)


    @istest
    def can_read_tab_element(self):
        element = xml_element("w:tab")
        tab = read_document_xml_element(element)
        assert_equal(documents.tab(), tab)
    
    @istest
    def unrecognised_elements_are_ignored(self):
        element = xml_element("w:huh", {}, [])
        assert_equal(None, read_document_xml_element(element))
    
    @istest
    def unrecognised_children_are_ignored(self):
        element = xml_element("w:r", {}, [_text_element("Hello!"), xml_element("w:huh", {}, [])])
        assert_equal(
            documents.run([documents.Text("Hello!")]),
            read_document_xml_element(element)
        )


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
    
