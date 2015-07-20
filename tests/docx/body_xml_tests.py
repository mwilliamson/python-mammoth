import io

from nose.tools import istest, assert_equal
import funk

from mammoth import documents, results
from mammoth.docx.xmlparser import element as xml_element, text as xml_text
from mammoth.docx import body_xml
from mammoth.docx.numbering_xml import Numbering
from mammoth.docx.relationships_xml import Relationships, Relationship
from mammoth.docx.styles_xml import Styles, Style


@istest
class ReadXmlElementTests(object):
    @istest
    def text_from_text_element_is_read(self):
        element = _text_element("Hello!")
        assert_equal(documents.Text("Hello!"), _read_and_get_document_xml_element(element))
    
    @istest
    def can_read_text_within_run(self):
        element = _run_element_with_text("Hello!")
        assert_equal(
            documents.run([documents.Text("Hello!")]),
            _read_and_get_document_xml_element(element)
        )
    
    @istest
    def can_read_text_within_paragraph(self):
        element = _paragraph_element_with_text("Hello!")
        assert_equal(
            documents.paragraph([documents.run([documents.Text("Hello!")])]),
            _read_and_get_document_xml_element(element)
        )
        
    @istest
    def paragraph_has_no_style_if_it_has_no_properties(self):
        element = xml_element("w:p")
        assert_equal(None, _read_and_get_document_xml_element(element).style_id)
        
    @istest
    def paragraph_has_style_id_read_from_paragraph_properties_if_present(self):
        style_xml = xml_element("w:pStyle", {"w:val": "Heading1"})
        properties_xml = xml_element("w:pPr", {}, [style_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        
        styles = Styles({"Heading1": Style(style_id="Heading1", name="Heading 1")}, {})
        
        paragraph = _read_and_get_document_xml_element(paragraph_xml, styles=styles)
        assert_equal("Heading1", paragraph.style_id)
        
    @istest
    def paragraph_has_style_name_read_from_paragraph_properties_and_styles(self):
        style_xml = xml_element("w:pStyle", {"w:val": "Heading1"})
        properties_xml = xml_element("w:pPr", {}, [style_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        
        styles = Styles({"Heading1": Style(style_id="Heading1", name="Heading 1")}, {})
        
        paragraph = _read_and_get_document_xml_element(paragraph_xml, styles=styles)
        assert_equal("Heading 1", paragraph.style_name)
        
    @istest
    def paragraph_has_no_numbering_if_it_has_no_numbering_properties(self):
        element = xml_element("w:p")
        assert_equal(None, _read_and_get_document_xml_element(element).numbering)
        
    @istest
    def paragraph_has_numbering_properties_from_paragraph_properties_if_present(self):
        numbering_properties_xml = xml_element("w:numPr", {}, [
            xml_element("w:ilvl", {"w:val": "1"}),
            xml_element("w:numId", {"w:val": "42"}),
        ])
        properties_xml = xml_element("w:pPr", {}, [numbering_properties_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        
        numbering = Numbering({"42": {"1": documents.numbering_level("1", True)}})
        paragraph = _read_and_get_document_xml_element(paragraph_xml, numbering=numbering)
        
        assert_equal("1", paragraph.numbering.level_index)
        assert_equal(True, paragraph.numbering.is_ordered)
    
    @istest
    def run_has_no_style_if_it_has_no_properties(self):
        element = xml_element("w:r")
        assert_equal(None, _read_and_get_document_xml_element(element).style_id)
        
    @istest
    def run_has_style_id_read_from_run_properties_if_present(self):
        style_xml = xml_element("w:rStyle", {"w:val": "Heading1Char"})
        
        styles = Styles({}, {"Heading1Char": Style(style_id="Heading1Char", name="Heading 1 Char")})
        
        run = self._read_run_with_properties([style_xml], styles=styles)
        assert_equal("Heading1Char", run.style_id)
        
    @istest
    def run_has_style_name_read_from_run_properties_and_styles(self):
        style_xml = xml_element("w:rStyle", {"w:val": "Heading1Char"})
        
        styles = Styles({}, {"Heading1Char": Style(style_id="Heading1Char", name="Heading 1 Char")})
        
        run = self._read_run_with_properties([style_xml], styles=styles)
        assert_equal("Heading 1 Char", run.style_name)
        
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
        
    @istest
    def run_is_not_underlined_if_underline_element_is_not_present(self):
        run = self._read_run_with_properties([])
        assert_equal(False, run.is_underline)
    
    @istest
    def run_is_underlined_if_underline_element_is_present(self):
        run = self._read_run_with_properties([xml_element("w:u")])
        assert_equal(True, run.is_underline)
        
    @istest
    def run_is_not_struckthrough_if_strikethrough_element_is_not_present(self):
        run = self._read_run_with_properties([])
        assert_equal(False, run.is_strikethrough)
    
    @istest
    def run_is_struckthrough_if_strikethrough_element_is_present(self):
        run = self._read_run_with_properties([xml_element("w:strike")])
        assert_equal(True, run.is_strikethrough)
    
    @istest
    def run_has_baseline_vertical_alignment_if_vertical_alignment_element_is_not_present(self):
        run = self._read_run_with_properties([])
        assert_equal(documents.VerticalAlignment.baseline, run.vertical_alignment)
        
    @istest
    def run_has_vertical_alignment_read_from_vertical_alignment_element(self):
        run = self._read_run_with_properties([xml_element("w:vertAlign", {"w:val": "superscript"})])
        assert_equal(documents.VerticalAlignment.superscript, run.vertical_alignment)
    
    def _read_run_with_properties(self, properties, styles=None):
        properties_xml = xml_element("w:rPr", {}, properties)
        run_xml = xml_element("w:r", {}, [properties_xml])
        return _read_and_get_document_xml_element(run_xml, styles=styles)


    @istest
    def can_read_tab_element(self):
        element = xml_element("w:tab")
        tab = _read_and_get_document_xml_element(element)
        assert_equal(documents.tab(), tab)
    
    
    @istest
    def word_table_is_read_as_document_table_element(self):
        element = xml_element("w:tbl", {}, [
            xml_element("w:tr", {}, [
                xml_element("w:tc", {}, [
                    xml_element("w:p", {}, [])
                ]),
            ]),
        ])
        table = _read_and_get_document_xml_element(element)
        expected_result = documents.table([
            documents.table_row([
                documents.table_cell([
                    documents.paragraph([])
                ])
            ])
        ])
        assert_equal(expected_result, table)


    @istest
    def children_of_w_ins_are_converted_normally(self):
        element = xml_element("w:p", {}, [
            xml_element("w:ins", {}, [
                xml_element("w:r")
            ])
        ])
        assert_equal(
            documents.paragraph([documents.run([])]),
            _read_and_get_document_xml_element(element)
        )
        
    @istest
    def children_of_w_smart_tag_are_converted_normally(self):
        element = xml_element("w:p", {}, [
            xml_element("w:smartTag", {}, [
                xml_element("w:r")
            ])
        ])
        assert_equal(
            documents.paragraph([documents.run([])]),
            _read_and_get_document_xml_element(element)
        )
        
    @istest
    def hyperlink_is_read_if_it_has_a_relationship_id(self):
        relationships = Relationships({
            "r42": Relationship(target="http://example.com")
        })
        run_element = xml_element("w:r")
        element = xml_element("w:hyperlink", {"r:id": "r42"}, [run_element])
        assert_equal(
            documents.hyperlink(href="http://example.com", children=[documents.run([])]),
            _read_and_get_document_xml_element(element, relationships=relationships)
        )
        
    @istest
    def hyperlink_is_read_if_it_has_an_anchor_attribute(self):
        run_element = xml_element("w:r")
        element = xml_element("w:hyperlink", {"w:anchor": "start"}, [run_element])
        assert_equal(
            documents.hyperlink(anchor="start", children=[documents.run([])]),
            _read_and_get_document_xml_element(element)
        )
        
    @istest
    def hyperlink_is_ignored_if_it_does_not_have_a_relationship_id_nor_anchor(self):
        run_element = xml_element("w:r")
        element = xml_element("w:hyperlink", {}, [run_element])
        assert_equal(
            [documents.run([])],
            _read_and_get_document_xml_element(element)
        )
        
    @istest
    def go_back_bookmark_is_ignored(self):
        element = xml_element("w:bookmarkStart", {"w:name": "_GoBack"})
        assert_equal(None, _read_and_get_document_xml_element(element))
        
    @istest
    def bookmark_start_is_read_if_name_is_not_go_back(self):
        element = xml_element("w:bookmarkStart", {"w:name": "start"})
        assert_equal(
            documents.bookmark("start"),
            _read_and_get_document_xml_element(element)
        )
    
    @istest
    def br_is_read_as_line_break(self):
        break_element = xml_element("w:br", {}, [])
        result = _read_and_get_document_xml_element(break_element)
        assert_equal(result, documents.line_break())
    
    
    @istest
    def warning_on_breaks_that_arent_line_breaks(self):
        break_element = xml_element("w:br", {"w:type": "page"}, [])
        result = _read_document_xml_element(break_element)
        expected_warning = results.warning("Unsupported break type: page")
        assert_equal([expected_warning], result.messages)
        assert_equal(None, result.value)
        
        
    @istest
    @funk.with_context
    def can_read_inline_pictures(self, context):
        drawing_element = _create_inline_image(
            blip=_embedded_blip("rId5"),
            description="It's a hat",
        )
        
        image_bytes = b"Not an image at all!"
        
        relationships = Relationships({
            "rId5": Relationship(target="media/hat.png")
        })
        
        docx_file = context.mock()
        funk.allows(docx_file).open("word/media/hat.png").returns(io.BytesIO(image_bytes))
        
        content_types = context.mock()
        funk.allows(content_types).find_content_type("word/media/hat.png").returns("image/png")
        
        image = _read_and_get_document_xml_element(
            drawing_element,
            content_types=content_types,
            relationships=relationships,
            docx_file=docx_file,
        )[0]
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(image_bytes, image_file.read())
        
    @istest
    @funk.with_context
    def can_read_anchored_pictures(self, context):
        drawing_element = _create_anchored_image(
            blip=_embedded_blip("rId5"),
            description="It's a hat",
        )
        
        image_bytes = b"Not an image at all!"
        
        relationships = Relationships({
            "rId5": Relationship(target="media/hat.png")
        })
        
        docx_file = context.mock()
        funk.allows(docx_file).open("word/media/hat.png").returns(io.BytesIO(image_bytes))
        
        content_types = context.mock()
        funk.allows(content_types).find_content_type("word/media/hat.png").returns("image/png")
        
        image = _read_and_get_document_xml_element(
            drawing_element,
            content_types=content_types,
            relationships=relationships,
            docx_file=docx_file,
        )[0]
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(image_bytes, image_file.read())
        
        
    @istest
    @funk.with_context
    def warning_if_unsupported_image_type(self, context):
        drawing_element = _create_inline_image(
            blip=_embedded_blip("rId5"),
            description="It's a hat",
        )
        
        image_bytes = b"Not an image at all!"
        
        relationships = Relationships({
            "rId5": Relationship(target="media/hat.emf")
        })
        
        docx_file = context.mock()
        funk.allows(docx_file).open("word/media/hat.emf").returns(io.BytesIO(image_bytes))
        
        content_types = context.mock()
        funk.allows(content_types).find_content_type("word/media/hat.emf").returns("image/x-emf")
        
        result = _read_document_xml_element(
            drawing_element,
            content_types=content_types,
            relationships=relationships,
            docx_file=docx_file,
        )
        assert_equal("image/x-emf", result.value[0].content_type)
        expected_warning = results.warning("Image of type image/x-emf is unlikely to display in web browsers")
        assert_equal([expected_warning], result.messages)
        
        
    @istest
    @funk.with_context
    def can_read_linked_pictures(self, context):
        drawing_element = _create_inline_image(
            blip=_linked_blip("rId5"),
            description="It's a hat",
        )
        
        image_bytes = b"Not an image at all!"
        
        relationships = Relationships({
            "rId5": Relationship(target="file:///media/hat.png")
        })
        
        files = context.mock()
        funk.allows(files).open("file:///media/hat.png").returns(io.BytesIO(image_bytes))
        
        content_types = context.mock()
        funk.allows(content_types).find_content_type("file:///media/hat.png").returns("image/png")
        
        image = _read_and_get_document_xml_element(
            drawing_element,
            content_types=content_types,
            relationships=relationships,
            files=files,
        )[0]
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(image_bytes, image_file.read())
    
    @istest
    def footnote_reference_has_id_read(self):
        footnote_xml = xml_element("w:footnoteReference", {"w:id": "4"})
        footnote = _read_and_get_document_xml_element(footnote_xml)
        assert_equal("4", footnote.note_id)
    
    @istest
    def ignored_elements_are_ignored_without_message(self):
        element = xml_element("w:bookmarkEnd")
        result = _read_document_xml_element(element)
        assert_equal(None, result.value)
        assert_equal([], result.messages)
    
    @istest
    def unrecognised_elements_emit_warning(self):
        element = xml_element("w:huh", {}, [])
        result = _read_document_xml_element(element)
        expected_warning = results.warning("An unrecognised element was ignored: w:huh")
        assert_equal([expected_warning], result.messages)
    
    @istest
    def unrecognised_elements_are_ignored(self):
        element = xml_element("w:huh", {}, [])
        assert_equal(None, _read_document_xml_element(element).value)
    
    @istest
    def unrecognised_children_are_ignored(self):
        element = xml_element("w:r", {}, [_text_element("Hello!"), xml_element("w:huh", {}, [])])
        assert_equal(
            documents.run([documents.Text("Hello!")]),
            _read_document_xml_element(element).value
        )
        
    @istest
    def text_boxes_have_content_appended_after_containing_paragraph(self):
        text_box = xml_element("w:pict", {}, [
            xml_element("v:shape", {}, [
                xml_element("v:textbox", {}, [
                    xml_element("w:txbxContent", {}, [
                        _paragraph_with_style_id("textbox-content")
                    ])
                ])
            ])
        ])
        paragraph = xml_element("w:p", {}, [
            xml_element("w:r", {}, [text_box])
        ])
        result = _read_and_get_document_xml_element(paragraph)
        assert_equal(result[1].style_id, "textbox-content")
    
    @istest
    def alternate_content_is_read_using_fallback(self):
        element = xml_element("mc:AlternateContent", {}, [
            xml_element("mc:Choice", {"Requires": "wps"}, [
                _paragraph_with_style_id("first")
            ]),
            xml_element("mc:Fallback", {}, [
                _paragraph_with_style_id("second")
            ])
        ])
        result = _read_and_get_document_xml_element(element)
        assert_equal("second", result[0].style_id)


def _read_and_get_document_xml_element(*args, **kwargs):
    styles = kwargs.pop("styles", FakeStyles())
    result = _read_document_xml_element(*args, styles=styles, **kwargs)
    assert_equal([], result.messages)
    return result.value


def _read_document_xml_element(element, *args, **kwargs):
    reader = body_xml.reader(*args, **kwargs)
    return reader.read(element)


class FakeStyles(object):
    def find_paragraph_style_by_id(self, style_id):
        return Style(style_id, style_id)

def _document_element_with_text(text):
    return xml_element("w:document", {}, [
        xml_element("w:body", {}, [_paragraph_element_with_text(text)])
    ])


def _paragraph_element_with_text(text):
    return xml_element("w:p", {}, [_run_element_with_text(text)])

def _paragraph_with_style_id(style_id):
    style_xml = xml_element("w:pStyle", {"w:val": style_id})
    properties_xml = xml_element("w:pPr", {}, [style_xml])
    return xml_element("w:p", {}, [properties_xml])

def _run_element_with_text(text):
    return xml_element("w:r", {}, [_text_element(text)])


def _text_element(value):
    return xml_element("w:t", {}, [xml_text(value)])
    

def _create_inline_image(description, blip):
    return xml_element("w:drawing", {}, [
        xml_element("wp:inline", {}, _create_image_elements(description, blip))
    ])


def _create_anchored_image(description, blip):
    return xml_element("w:drawing", {}, [
        xml_element("wp:anchor", {}, _create_image_elements(description, blip))
    ])

    
def _create_image_elements(description, blip):
    return [
        xml_element("wp:docPr", {"descr": description}),
        xml_element("a:graphic", {}, [
            xml_element("a:graphicData", {}, [
                xml_element("pic:pic", {}, [
                    xml_element("pic:blipFill", {}, [
                        blip
                    ])
                ])
            ])
        ])
    ]

def _embedded_blip(relationship_id):
    return _blip({"r:embed": relationship_id})

def _linked_blip(relationship_id):
    return _blip({"r:link": relationship_id})

def _blip(attributes):
    return xml_element("a:blip", attributes)
