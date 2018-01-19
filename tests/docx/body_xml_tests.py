import io
import sys

from precisely import assert_that, is_sequence
from nose.tools import istest, assert_equal
from nose_parameterized import parameterized, param
import funk

from mammoth import documents, results
from mammoth.docx.xmlparser import element as xml_element, text as xml_text
from mammoth.docx import body_xml
from mammoth.docx.numbering_xml import Numbering
from mammoth.docx.relationships_xml import Relationships, Relationship
from mammoth.docx.styles_xml import Styles, Style
from .document_matchers import (
    is_paragraph,
    is_empty_run,
    is_run,
    is_hyperlink,
    is_text,
    is_table,
    is_row,
)

if sys.version_info >= (3, ):
    unichr = chr


@istest
def text_from_text_element_is_read():
    element = _text_element("Hello!")
    assert_equal(documents.Text("Hello!"), _read_and_get_document_xml_element(element))


@istest
def can_read_text_within_run():
    element = _run_element_with_text("Hello!")
    assert_equal(
        documents.run([documents.Text("Hello!")]),
        _read_and_get_document_xml_element(element)
    )

@istest
def can_read_text_within_paragraph():
    element = _paragraph_element_with_text("Hello!")
    assert_equal(
        documents.paragraph([documents.run([documents.Text("Hello!")])]),
        _read_and_get_document_xml_element(element)
    )


@istest
class ParagraphTests(object):
    @istest
    def paragraph_has_no_style_if_it_has_no_properties(self):
        element = xml_element("w:p")
        assert_equal(None, _read_and_get_document_xml_element(element).style_id)
        
    @istest
    def paragraph_has_style_id_and_name_read_from_paragraph_properties_if_present(self):
        style_xml = xml_element("w:pStyle", {"w:val": "Heading1"})
        properties_xml = xml_element("w:pPr", {}, [style_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        
        styles = Styles(
            paragraph_styles={"Heading1": Style(style_id="Heading1", name="Heading 1")},
            character_styles={},
            table_styles={},
        )
        
        paragraph = _read_and_get_document_xml_element(paragraph_xml, styles=styles)
        assert_equal("Heading1", paragraph.style_id)
        assert_equal("Heading 1", paragraph.style_name)
        
    @istest
    def warning_is_emitted_when_paragraph_style_cannot_be_found(self):
        style_xml = xml_element("w:pStyle", {"w:val": "Heading1"})
        properties_xml = xml_element("w:pPr", {}, [style_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        
        result = _read_document_xml_element(paragraph_xml, styles=Styles.EMPTY)
        paragraph = result.value
        assert_equal("Heading1", paragraph.style_id)
        assert_equal(None, paragraph.style_name)
        assert_equal([results.warning("Paragraph style with ID Heading1 was referenced but not defined in the document")], result.messages)
        
    @istest
    def paragraph_has_no_justification_if_it_has_no_justificiation_properties(self):
        paragraph_xml = xml_element("w:p")
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal(None, paragraph.alignment)
        
    @istest
    def paragraph_has_justification_read_from_paragraph_properties_if_present(self):
        justification_xml = xml_element("w:jc", {"w:val": "center"})
        properties_xml = xml_element("w:pPr", {}, [justification_xml])
        paragraph_xml = xml_element("w:p", {}, [properties_xml])
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal("center", paragraph.alignment)
    
    @istest
    def paragraph_has_no_numbering_if_it_has_no_numbering_properties(self):
        element = xml_element("w:p")
        assert_equal(None, _read_and_get_document_xml_element(element).numbering)
        
    @istest
    def paragraph_has_numbering_properties_from_paragraph_properties_if_present(self):
        paragraph_xml = self._paragraph_with_numbering_properties([
            xml_element("w:ilvl", {"w:val": "1"}),
            xml_element("w:numId", {"w:val": "42"}),
        ])
        
        numbering = Numbering({"42": {"1": documents.numbering_level("1", True)}})
        paragraph = _read_and_get_document_xml_element(paragraph_xml, numbering=numbering)
        
        assert_equal("1", paragraph.numbering.level_index)
        assert_equal(True, paragraph.numbering.is_ordered)
        
    @istest
    def numbering_properties_are_ignored_if_lvl_is_missing(self):
        paragraph_xml = self._paragraph_with_numbering_properties([
            xml_element("w:numId", {"w:val": "42"}),
        ])
        
        numbering = Numbering({"42": {"1": documents.numbering_level("1", True)}})
        paragraph = _read_and_get_document_xml_element(paragraph_xml, numbering=numbering)
        
        assert_equal(None, paragraph.numbering)
        
    @istest
    def numbering_properties_are_ignored_if_num_id_is_missing(self):
        paragraph_xml = self._paragraph_with_numbering_properties([
            xml_element("w:ilvl", {"w:val": "1"}),
        ])
        
        numbering = Numbering({"42": {"1": documents.numbering_level("1", True)}})
        paragraph = _read_and_get_document_xml_element(paragraph_xml, numbering=numbering)
        
        assert_equal(None, paragraph.numbering)
    
    def _paragraph_with_numbering_properties(self, children):
        numbering_properties_xml = xml_element("w:numPr", {}, children)
        properties_xml = xml_element("w:pPr", {}, [numbering_properties_xml])
        return xml_element("w:p", {}, [properties_xml])


@istest
class ParagraphIndentTests(object):
    @istest
    def when_w_start_is_set_then_start_indent_is_read_from_w_start(self):
        paragraph_xml = self._paragraph_with_indent({"w:start": "720", "w:left": "40"})
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal("720", paragraph.indent.start)
    
    @istest
    def when_w_start_is_not_set_then_start_indent_is_read_from_w_left(self):
        paragraph_xml = self._paragraph_with_indent({"w:left": "720"})
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal("720", paragraph.indent.start)

    @istest
    def when_w_end_is_set_then_end_indent_is_read_from_w_end(self):
        paragraph_xml = self._paragraph_with_indent({"w:end": "720", "w:right": "40"})
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal("720", paragraph.indent.end)

    @istest
    def when_w_end_is_not_set_then_end_indent_is_read_from_w_right(self):
        paragraph_xml = self._paragraph_with_indent({"w:right": "720"})
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal("720", paragraph.indent.end)

    @istest
    def paragraph_has_indent_first_line_read_from_paragraph_properties_if_present(self):
        paragraph_xml = self._paragraph_with_indent({"w:firstLine": "720"})
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal("720", paragraph.indent.first_line)

    @istest
    def paragraph_has_indent_hanging_read_from_paragraph_properties_if_present(self):
        paragraph_xml = self._paragraph_with_indent({"w:hanging": "720"})
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal("720", paragraph.indent.hanging)

    @istest
    def when_indent_attributes_arent_set_then_indents_are_none(self):
        paragraph_xml = self._paragraph_with_indent({})
        paragraph = _read_and_get_document_xml_element(paragraph_xml)
        assert_equal(None, paragraph.indent.start)
        assert_equal(None, paragraph.indent.end)
        assert_equal(None, paragraph.indent.first_line)
        assert_equal(None, paragraph.indent.hanging)
    
    def _paragraph_with_indent(self, attributes):
        indent_xml = xml_element("w:ind", attributes)
        properties_xml = xml_element("w:pPr", {}, [indent_xml])
        return xml_element("w:p", {}, [properties_xml])


@istest
class RunTests(object):
    @istest
    def run_has_no_style_if_it_has_no_properties(self):
        element = xml_element("w:r")
        assert_equal(None, _read_and_get_document_xml_element(element).style_id)
        
    @istest
    def run_has_style_id_and_name_read_from_run_properties_if_present(self):
        style_xml = xml_element("w:rStyle", {"w:val": "Heading1Char"})
        
        styles = Styles(
            paragraph_styles={},
            character_styles={"Heading1Char": Style(style_id="Heading1Char", name="Heading 1 Char")},
            table_styles={},
        )
        
        run = self._read_run_with_properties([style_xml], styles=styles)
        assert_equal("Heading1Char", run.style_id)
        assert_equal("Heading 1 Char", run.style_name)
        
    @istest
    def warning_is_emitted_when_run_style_cannot_be_found(self):
        style_xml = xml_element("w:rStyle", {"w:val": "Heading1Char"})
        properties_xml = xml_element("w:rPr", {}, [style_xml])
        run_xml = xml_element("w:r", {}, [properties_xml])
        
        result = _read_document_xml_element(run_xml, styles=Styles.EMPTY)
        run = result.value
        assert_equal("Heading1Char", run.style_id)
        assert_equal(None, run.style_name)
        assert_equal([results.warning("Run style with ID Heading1Char was referenced but not defined in the document")], result.messages)
        
        
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
    def run_is_not_small_caps_if_small_caps_element_is_not_present(self):
        run = self._read_run_with_properties([])
        assert_equal(False, run.is_small_caps)
    
    @istest
    def run_is_small_caps_if_small_caps_element_is_present(self):
        run = self._read_run_with_properties([xml_element("w:smallCaps")])
        assert_equal(True, run.is_small_caps)

    run_boolean_property_test = lambda func: parameterized([
        param(attr_name="is_bold", tag_name="w:b"),
        param(attr_name="is_underline", tag_name="w:u"),
        param(attr_name="is_italic", tag_name="w:i"),
        param(attr_name="is_strikethrough", tag_name="w:strike"),
        param(attr_name="is_small_caps", tag_name="w:smallCaps"),
    ])(istest(func))

    @run_boolean_property_test
    def run_boolean_property_is_false_if_element_is_present_and_val_is_false(self, attr_name, tag_name):
        run = self._read_run_with_properties([xml_element(tag_name, {"w:val": "false"})])
        assert_equal(False, getattr(run, attr_name))

    @run_boolean_property_test
    def run_boolean_property_is_false_if_element_is_present_and_val_is_0(self, attr_name, tag_name):
        run = self._read_run_with_properties([xml_element(tag_name, {"w:val": "0"})])
        assert_equal(False, getattr(run, attr_name))

    @run_boolean_property_test
    def run_boolean_property_is_true_if_element_is_present_and_val_is_true(self, attr_name, tag_name):
        run = self._read_run_with_properties([xml_element(tag_name, {"w:val": "true"})])
        assert_equal(True, getattr(run, attr_name))

    @run_boolean_property_test
    def run_boolean_property_is_true_if_element_is_present_and_val_is_1(self, attr_name, tag_name):
        run = self._read_run_with_properties([xml_element(tag_name, {"w:val": "1"})])
        assert_equal(True, getattr(run, attr_name))
    
    @istest
    def run_has_baseline_vertical_alignment_if_vertical_alignment_element_is_not_present(self):
        run = self._read_run_with_properties([])
        assert_equal(documents.VerticalAlignment.baseline, run.vertical_alignment)
        
    @istest
    def run_has_vertical_alignment_read_from_vertical_alignment_element(self):
        run = self._read_run_with_properties([xml_element("w:vertAlign", {"w:val": "superscript"})])
        assert_equal(documents.VerticalAlignment.superscript, run.vertical_alignment)

    @istest
    def run_has_none_font_by_default(self):
        run = self._read_run_with_properties([])
        assert_equal(None, run.font)

    @istest
    def run_has_font_read_from_properties(self):
        font_xml = xml_element("w:rFonts", {"w:ascii": "Arial"})
        run = self._read_run_with_properties([font_xml])
        assert_equal("Arial", run.font)
    
    def _read_run_with_properties(self, properties, styles=None):
        properties_xml = xml_element("w:rPr", {}, properties)
        run_xml = xml_element("w:r", {}, [properties_xml])
        return _read_and_get_document_xml_element(run_xml, styles=styles)


@istest
class ComplexFieldTests(object):
    _URI = "http://example.com"
    _BEGIN_COMPLEX_FIELD = xml_element("w:r", {}, [
        xml_element("w:fldChar", {"w:fldCharType": "begin"}),
    ])
    _SEPARATE_COMPLEX_FIELD = xml_element("w:r", {}, [
        xml_element("w:fldChar", {"w:fldCharType": "separate"}),
    ])
    _END_COMPLEX_FIELD = xml_element("w:r", {}, [
        xml_element("w:fldChar", {"w:fldCharType": "end"}),
    ])
    _HYPERLINK_INSTRTEXT = xml_element("w:instrText", {}, [
        xml_text(' HYPERLINK "{0}"'.format(_URI))
    ])
    
    def _is_hyperlinked_run(self, **kwargs):
        return is_run(children=is_sequence(
            is_hyperlink(
                href=self._URI,
                **kwargs
            ),
        ))
    
    @property
    def _is_empty_hyperlinked_run(self):
        return self._is_hyperlinked_run(children=[])
    
    @istest
    def runs_in_a_complex_field_for_hyperlinks_are_read_as_hyperlinks(self):
        element = xml_element("w:p", {}, [
            self._BEGIN_COMPLEX_FIELD,
            self._HYPERLINK_INSTRTEXT,
            self._SEPARATE_COMPLEX_FIELD,
            _run_element_with_text("this is a hyperlink"),
            self._END_COMPLEX_FIELD,
        ])
        paragraph = _read_and_get_document_xml_element(element)

        assert_that(paragraph, is_paragraph(children=is_sequence(
            is_empty_run,
            self._is_empty_hyperlinked_run,
            self._is_hyperlinked_run(children=is_sequence(
                is_text("this is a hyperlink"),
            )),
            is_empty_run,
        )))
    
    @istest
    def runs_after_a_complex_field_for_hyperlinks_are_not_read_as_hyperlinks(self):
        element = xml_element("w:p", {}, [
            self._BEGIN_COMPLEX_FIELD,
            self._HYPERLINK_INSTRTEXT,
            self._SEPARATE_COMPLEX_FIELD,
            self._END_COMPLEX_FIELD,
            _run_element_with_text("this will not be a hyperlink"),
        ])
        paragraph = _read_and_get_document_xml_element(element)

        assert_that(paragraph, is_paragraph(children=is_sequence(
            is_empty_run,
            self._is_empty_hyperlinked_run,
            is_empty_run,
            is_run(children=is_sequence(
                is_text("this will not be a hyperlink"),
            )),
        )))
    
    @istest
    def can_handle_split_instr_text_elements(self):
        element = xml_element("w:p", {}, [
            self._BEGIN_COMPLEX_FIELD,
            xml_element("w:instrText", {}, [
                xml_text(" HYPE")
            ]),
            xml_element("w:instrText", {}, [
                xml_text('RLINK "{0}"'.format(self._URI)),
            ]),
            self._SEPARATE_COMPLEX_FIELD,
            _run_element_with_text("this is a hyperlink"),
            self._END_COMPLEX_FIELD,
        ])
        paragraph = _read_and_get_document_xml_element(element)

        assert_that(paragraph, is_paragraph(children=is_sequence(
            is_empty_run,
            self._is_empty_hyperlinked_run,
            self._is_hyperlinked_run(children=is_sequence(
                is_text("this is a hyperlink"),
            )),
            is_empty_run,
        )))
    
    @istest
    def hyperlink_is_not_ended_by_end_of_nested_complex_field(self):
        element = xml_element("w:p", {}, [
            self._BEGIN_COMPLEX_FIELD,
            self._HYPERLINK_INSTRTEXT,
            self._SEPARATE_COMPLEX_FIELD,
            self._BEGIN_COMPLEX_FIELD,
            xml_element("w:instrText", {}, [
                xml_text(' AUTHOR "John Doe"')
            ]),
            self._SEPARATE_COMPLEX_FIELD,
            self._END_COMPLEX_FIELD,
            _run_element_with_text("this is a hyperlink"),
            self._END_COMPLEX_FIELD,
        ])
        paragraph = _read_and_get_document_xml_element(element)

        assert_that(paragraph, is_paragraph(children=is_sequence(
            is_empty_run,
            self._is_empty_hyperlinked_run,
            self._is_empty_hyperlinked_run,
            self._is_empty_hyperlinked_run,
            self._is_empty_hyperlinked_run,
            self._is_hyperlinked_run(children=is_sequence(
                is_text("this is a hyperlink"),
            )),
            is_empty_run,
        )))
    
    @istest
    def complex_field_nested_within_a_hyperlink_complex_field_is_wrapped_with_the_hyperlink(self):
        element = xml_element("w:p", {}, [
            self._BEGIN_COMPLEX_FIELD,
            self._HYPERLINK_INSTRTEXT,
            self._SEPARATE_COMPLEX_FIELD,
            self._BEGIN_COMPLEX_FIELD,
            xml_element("w:instrText", {}, [
                xml_text(' AUTHOR "John Doe"')
            ]),
            self._SEPARATE_COMPLEX_FIELD,
            _run_element_with_text("John Doe"),
            self._END_COMPLEX_FIELD,
            self._END_COMPLEX_FIELD,
        ])
        paragraph = _read_and_get_document_xml_element(element)

        assert_that(paragraph, is_paragraph(children=is_sequence(
            is_empty_run,
            self._is_empty_hyperlinked_run,
            self._is_empty_hyperlinked_run,
            self._is_empty_hyperlinked_run,
            self._is_hyperlinked_run(children=is_sequence(
                is_text("John Doe"),
            )),
            self._is_empty_hyperlinked_run,
            is_empty_run,
        )))
    
    @istest
    def field_without_separate_fld_char_is_ignored(self):
        element = xml_element("w:p", {}, [
            self._BEGIN_COMPLEX_FIELD,
            self._HYPERLINK_INSTRTEXT,
            self._SEPARATE_COMPLEX_FIELD,
            self._BEGIN_COMPLEX_FIELD,
            self._END_COMPLEX_FIELD,
            _run_element_with_text("this is a hyperlink"),
            self._END_COMPLEX_FIELD,
        ])
        paragraph = _read_and_get_document_xml_element(element)

        assert_that(paragraph, is_paragraph(children=is_sequence(
            is_empty_run,
            self._is_empty_hyperlinked_run,
            self._is_empty_hyperlinked_run,
            self._is_empty_hyperlinked_run,
            self._is_hyperlinked_run(children=is_sequence(
                is_text("this is a hyperlink"),
            )),
            is_empty_run,
        )))


@istest
def can_read_tab_element():
    element = xml_element("w:tab")
    tab = _read_and_get_document_xml_element(element)
    assert_equal(documents.tab(), tab)


@istest
def no_break_hyphen_element_is_read_as_non_breaking_hyphen_character():
    element = xml_element("w:noBreakHyphen")
    tab = _read_and_get_document_xml_element(element)
    assert_equal(documents.text(unichr(0x2011)), tab)
    

@istest
class TableTests(object):
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
    def table_has_no_style_if_it_has_no_properties(self):
        element = xml_element("w:tbl")
        assert_equal(None, _read_and_get_document_xml_element(element).style_id)
        
    @istest
    def table_has_style_id_and_name_read_from_paragraph_properties_if_present(self):
        style_xml = xml_element("w:tblStyle", {"w:val": "TableNormal"})
        properties_xml = xml_element("w:tblPr", {}, [style_xml])
        table_xml = xml_element("w:tbl", {}, [properties_xml])
        
        styles = Styles(
            paragraph_styles={},
            character_styles={},
            table_styles={"TableNormal": Style(style_id="TableNormal", name="Normal Table")},
        )
        
        paragraph = _read_and_get_document_xml_element(table_xml, styles=styles)
        assert_equal("TableNormal", paragraph.style_id)
        assert_equal("Normal Table", paragraph.style_name)
        
    @istest
    def warning_is_emitted_when_table_style_cannot_be_found(self):
        style_xml = xml_element("w:tblStyle", {"w:val": "TableNormal"})
        properties_xml = xml_element("w:tblPr", {}, [style_xml])
        table_xml = xml_element("w:tbl", {}, [properties_xml])
        
        result = _read_document_xml_element(table_xml, styles=Styles.EMPTY)
        table = result.value
        assert_equal("TableNormal", table.style_id)
        assert_equal(None, table.style_name)
        assert_equal([results.warning("Table style with ID TableNormal was referenced but not defined in the document")], result.messages)
    
    @istest
    def tbl_header_marks_table_row_as_header(self):
        element = xml_element("w:tbl", {}, [
            xml_element("w:tr", {}, [
                xml_element("w:trPr", {}, [
                    xml_element("w:tblHeader")
                ]),
            ]),
            xml_element("w:tr"),
        ])
        table = _read_and_get_document_xml_element(element)
        assert_that(table, is_table(
            children=is_sequence(
                is_row(is_header=True),
                is_row(is_header=False),
            ),
        ))
    
    
    @istest
    def gridspan_is_read_as_colspan_for_table_cell(self):
        element = xml_element("w:tbl", {}, [
            xml_element("w:tr", {}, [
                xml_element("w:tc", {}, [
                    xml_element("w:tcPr", {}, [
                        xml_element("w:gridSpan", {"w:val": "2"})
                    ]),
                    xml_element("w:p", {}, [])
                ]),
            ]),
        ])
        table = _read_and_get_document_xml_element(element)
        expected_result = documents.table([
            documents.table_row([
                documents.table_cell([
                    documents.paragraph([])
                ], colspan=2)
            ])
        ])
        assert_equal(expected_result, table)


    @istest
    def vmerge_is_read_as_rowspan_for_table_cell(self):
        element = xml_element("w:tbl", {}, [
            w_tr(w_tc()),
            w_tr(w_tc(properties=[w_vmerge("restart")])),
            w_tr(w_tc(properties=[w_vmerge("continue")])),
            w_tr(w_tc(properties=[w_vmerge("continue")])),
            w_tr(w_tc())
        ])
        result = _read_and_get_document_xml_element(element)
        expected_result = documents.table([
            documents.table_row([documents.table_cell([])]),
            documents.table_row([documents.table_cell([], rowspan=3)]),
            documents.table_row([]),
            documents.table_row([]),
            documents.table_row([documents.table_cell([])]),
        ])
        assert_equal(expected_result, result)


    @istest
    def vmerge_without_val_is_treated_as_continue(self):
        element = xml_element("w:tbl", {}, [
            w_tr(w_tc(properties=[w_vmerge("restart")])),
            w_tr(w_tc(properties=[w_vmerge(None)])),
        ])
        result = _read_and_get_document_xml_element(element)
        expected_result = documents.table([
            documents.table_row([documents.table_cell([], rowspan=2)]),
            documents.table_row([]),
        ])
        assert_equal(expected_result, result)


    @istest
    def vmerge_accounts_for_cells_spanning_columns(self):
        element = xml_element("w:tbl", {}, [
            w_tr(w_tc(), w_tc(), w_tc(properties=[w_vmerge("restart")])),
            w_tr(w_tc(properties=[w_gridspan("2")]), w_tc(properties=[w_vmerge("continue")])),
            w_tr(w_tc(), w_tc(), w_tc(properties=[w_vmerge("continue")])),
            w_tr(w_tc(), w_tc(), w_tc()),
        ])
        result = _read_and_get_document_xml_element(element)
        expected_result = documents.table([
            documents.table_row([documents.table_cell([]), documents.table_cell([]), documents.table_cell([], rowspan=3)]),
            documents.table_row([documents.table_cell([], colspan=2)]),
            documents.table_row([documents.table_cell([]), documents.table_cell([])]),
            documents.table_row([documents.table_cell([]), documents.table_cell([]), documents.table_cell([])]),
        ])
        assert_equal(expected_result, result)


    @istest
    def no_vertical_cell_merging_if_merged_cells_do_not_line_up(self):
        element = xml_element("w:tbl", {}, [
            w_tr(w_tc(properties=[w_gridspan("2")]), w_tc(properties=[w_vmerge("restart")])),
            w_tr(w_tc(), w_tc(properties=[w_vmerge("continue")])),
        ])
        result = _read_and_get_document_xml_element(element)
        expected_result = documents.table([
            documents.table_row([documents.table_cell([], colspan=2), documents.table_cell([])]),
            documents.table_row([documents.table_cell([]), documents.table_cell([])]),
        ])
        assert_equal(expected_result, result)


    @istest
    def warning_if_non_row_in_table(self):
        element = xml_element("w:tbl", {}, [xml_element("w:p")])
        result = _read_document_xml_element(element)
        expected_warning = results.warning("unexpected non-row element in table, cell merging may be incorrect")
        assert_equal([expected_warning], result.messages)


    @istest
    def warning_if_non_cell_in_table_row(self):
        element = xml_element("w:tbl", {}, [w_tr(xml_element("w:p"))])
        result = _read_document_xml_element(element)
        expected_warning = results.warning("unexpected non-cell element in table row, cell merging may be incorrect")
        assert_equal([expected_warning], result.messages)


@istest
def children_of_w_ins_are_converted_normally():
    _assert_children_are_converted_normally("w:ins")
    
@istest
def children_of_w_object_are_converted_normally():
    _assert_children_are_converted_normally("w:object")

@istest
def children_of_w_smart_tag_are_converted_normally():
    _assert_children_are_converted_normally("w:smartTag")


@istest
def children_of_v_group_are_converted_normally():
    _assert_children_are_converted_normally("v:group")


def _assert_children_are_converted_normally(tag_name):
    element = xml_element("w:p", {}, [
        xml_element(tag_name, {}, [
            xml_element("w:r")
        ])
    ])
    assert_equal(
        documents.paragraph([documents.run([])]),
        _read_and_get_document_xml_element(element)
    )


@istest
class HyperlinkTests(object):
    @istest
    def hyperlink_is_read_as_external_hyperlink_if_it_has_a_relationship_id(self):
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
    def hyperlink_is_read_as_external_hyperlink_if_it_has_a_relationship_id_and_an_anchor(self):
        relationships = Relationships({
            "r42": Relationship(target="http://example.com/")
        })
        run_element = xml_element("w:r")
        element = xml_element("w:hyperlink", {"r:id": "r42", "w:anchor": "fragment"}, [run_element])
        assert_equal(
            documents.hyperlink(href="http://example.com/#fragment", children=[documents.run([])]),
            _read_and_get_document_xml_element(element, relationships=relationships)
        )
        
    @istest
    def existing_fragment_is_replaced_when_anchor_is_set_on_external_link(self):
        relationships = Relationships({
            "r42": Relationship(target="http://example.com/#previous")
        })
        run_element = xml_element("w:r")
        element = xml_element("w:hyperlink", {"r:id": "r42", "w:anchor": "fragment"}, [run_element])
        assert_equal(
            documents.hyperlink(href="http://example.com/#fragment", children=[documents.run([])]),
            _read_and_get_document_xml_element(element, relationships=relationships)
        )
        
    @istest
    def hyperlink_is_read_as_internal_hyperlink_if_it_has_an_anchor_attribute(self):
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
            documents.run([]),
            _read_and_get_document_xml_element(element)
        )
        
    @istest
    def target_frame_is_read(self):
        element = xml_element("w:hyperlink", {
            "w:anchor": "start",
            "w:tgtFrame": "_blank",
        })
        assert_that(
            _read_and_get_document_xml_element(element),
            is_hyperlink(target_frame="_blank"),
        )
        
    @istest
    def empty_target_frame_is_ignored(self):
        element = xml_element("w:hyperlink", {
            "w:anchor": "start",
            "w:tgtFrame": "",
        })
        assert_that(
            _read_and_get_document_xml_element(element),
            is_hyperlink(target_frame=None),
        )


@istest
class BookmarkTests(object):
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
class BreakTests(object):
    @istest
    def br_without_explicit_type_is_read_as_line_break(self):
        break_element = xml_element("w:br", {}, [])
        result = _read_document_xml_element(break_element)
        assert_equal(documents.line_break, result.value)

    @istest
    def br_with_text_wrapping_type_is_read_as_line_break(self):
        break_element = xml_element("w:br", {"w:type": "textWrapping"}, [])
        result = _read_document_xml_element(break_element)
        assert_equal(documents.line_break, result.value)

    @istest
    def br_with_page_type_is_read_as_page_break(self):
        break_element = xml_element("w:br", {"w:type": "page"}, [])
        result = _read_document_xml_element(break_element)
        assert_equal(documents.page_break, result.value)

    @istest
    def br_with_column_type_is_read_as_column_break(self):
        break_element = xml_element("w:br", {"w:type": "column"}, [])
        result = _read_document_xml_element(break_element)
        assert_equal(documents.column_break, result.value)

    @istest
    def warning_on_break_types_that_arent_recognised(self):
        break_element = xml_element("w:br", {"w:type": "unknownBreakType"}, [])
        result = _read_document_xml_element(break_element)
        expected_warning = results.warning("Unsupported break type: unknownBreakType")
        assert_equal([expected_warning], result.messages)
        assert_equal(None, result.value)


@istest
class ImageTests(object):
    IMAGE_BYTES = b"Not an image at all!"
    IMAGE_RELATIONSHIP_ID = "rId5"
    
    def _read_embedded_image(self, element):
        relationships = Relationships({
            self.IMAGE_RELATIONSHIP_ID: Relationship(target="media/hat.png")
        })
        
        mocks = funk.Mocks()
        docx_file = mocks.mock()
        funk.allows(docx_file).open("word/media/hat.png").returns(io.BytesIO(self.IMAGE_BYTES))
        
        content_types = mocks.mock()
        funk.allows(content_types).find_content_type("word/media/hat.png").returns("image/png")
        
        return _read_and_get_document_xml_element(
            element,
            content_types=content_types,
            relationships=relationships,
            docx_file=docx_file,
        )
    
    @istest
    def can_read_imagedata_elements_with_rid_attribute(self):
        imagedata_element = xml_element("v:imagedata", {
            "r:id": self.IMAGE_RELATIONSHIP_ID,
            "o:title": "It's a hat"
        })
        
        image = self._read_embedded_image(imagedata_element)
        
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(self.IMAGE_BYTES, image_file.read())
    
    @istest
    def when_imagedata_element_has_no_relationship_id_then_it_is_ignored_with_warning(self):
        imagedata_element = xml_element("v:imagedata")
        
        result = _read_document_xml_element(imagedata_element)
        expected_warning = results.warning("A v:imagedata element without a relationship ID was ignored")
        assert_equal([expected_warning], result.messages)
        assert_equal(None, result.value)
        
        
    @istest
    def can_read_inline_pictures(self):
        drawing_element = _create_inline_image(
            blip=_embedded_blip(self.IMAGE_RELATIONSHIP_ID),
            description="It's a hat",
        )
        
        image = self._read_embedded_image(drawing_element)
        
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(self.IMAGE_BYTES, image_file.read())
        
        
    @istest
    def alt_text_title_is_used_if_alt_text_description_is_blank(self):
        drawing_element = _create_inline_image(
            blip=_embedded_blip(self.IMAGE_RELATIONSHIP_ID),
            description=" ",
            title="It's a hat",
        )
        
        image = self._read_embedded_image(drawing_element)
        
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(self.IMAGE_BYTES, image_file.read())
        
        
    @istest
    def alt_text_title_is_used_if_alt_text_description_is_missing(self):
        drawing_element = _create_inline_image(
            blip=_embedded_blip(self.IMAGE_RELATIONSHIP_ID),
            title="It's a hat",
        )
        
        image = self._read_embedded_image(drawing_element)
        
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(self.IMAGE_BYTES, image_file.read())
        
        
    @istest
    def alt_text_description_is_preferred_to_alt_text_title(self):
        drawing_element = _create_inline_image(
            blip=_embedded_blip(self.IMAGE_RELATIONSHIP_ID),
            description="It's a hat",
            title="hat",
        )
        
        image = self._read_embedded_image(drawing_element)
        
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(self.IMAGE_BYTES, image_file.read())
        
    @istest
    def can_read_anchored_pictures(self):
        drawing_element = _create_anchored_image(
            blip=_embedded_blip(self.IMAGE_RELATIONSHIP_ID),
            description="It's a hat",
        )
        
        image = self._read_embedded_image(drawing_element)
        
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(self.IMAGE_BYTES, image_file.read())
        
        
    @istest
    @funk.with_mocks
    def warning_if_unsupported_image_type(self, mocks):
        drawing_element = _create_inline_image(
            blip=_embedded_blip("rId5"),
            description="It's a hat",
        )
        
        relationships = Relationships({
            "rId5": Relationship(target="media/hat.emf")
        })
        
        docx_file = mocks.mock()
        funk.allows(docx_file).open("word/media/hat.emf").returns(io.BytesIO(self.IMAGE_BYTES))
        
        content_types = mocks.mock()
        funk.allows(content_types).find_content_type("word/media/hat.emf").returns("image/x-emf")
        
        result = _read_document_xml_element(
            drawing_element,
            content_types=content_types,
            relationships=relationships,
            docx_file=docx_file,
        )
        assert_equal("image/x-emf", result.value.content_type)
        expected_warning = results.warning("Image of type image/x-emf is unlikely to display in web browsers")
        assert_equal([expected_warning], result.messages)
        
        
    @istest
    @funk.with_mocks
    def can_read_linked_pictures(self, mocks):
        drawing_element = _create_inline_image(
            blip=_linked_blip("rId5"),
            description="It's a hat",
        )
        
        relationships = Relationships({
            "rId5": Relationship(target="file:///media/hat.png")
        })
        
        files = mocks.mock()
        funk.allows(files).verify("file:///media/hat.png")
        funk.allows(files).open("file:///media/hat.png").returns(io.BytesIO(self.IMAGE_BYTES))
        
        content_types = mocks.mock()
        funk.allows(content_types).find_content_type("file:///media/hat.png").returns("image/png")
        
        image = _read_and_get_document_xml_element(
            drawing_element,
            content_types=content_types,
            relationships=relationships,
            files=files,
        )
        assert_equal(documents.Image, type(image))
        assert_equal("It's a hat", image.alt_text)
        assert_equal("image/png", image.content_type)
        with image.open() as image_file:
            assert_equal(self.IMAGE_BYTES, image_file.read())


@istest
def footnote_reference_has_id_read():
    footnote_xml = xml_element("w:footnoteReference", {"w:id": "4"})
    footnote = _read_and_get_document_xml_element(footnote_xml)
    assert_equal("4", footnote.note_id)

@istest
def comment_reference_has_id_read():
    comment_reference_xml = xml_element("w:commentReference", {"w:id": "4"})
    comment_reference = _read_and_get_document_xml_element(comment_reference_xml)
    assert_equal(documents.CommentReference("4"), comment_reference)

@istest
def ignored_elements_are_ignored_without_message():
    element = xml_element("w:bookmarkEnd")
    result = _read_document_xml_element(element)
    assert_equal(None, result.value)
    assert_equal([], result.messages)

@istest
def unrecognised_elements_emit_warning():
    element = xml_element("w:huh", {}, [])
    result = _read_document_xml_element(element)
    expected_warning = results.warning("An unrecognised element was ignored: w:huh")
    assert_equal([expected_warning], result.messages)

@istest
def unrecognised_elements_are_ignored():
    element = xml_element("w:huh", {}, [])
    assert_equal(None, _read_document_xml_element(element).value)

@istest
def unrecognised_children_are_ignored():
    element = xml_element("w:r", {}, [_text_element("Hello!"), xml_element("w:huh", {}, [])])
    assert_equal(
        documents.run([documents.Text("Hello!")]),
        _read_document_xml_element(element).value
    )
    
@istest
def text_boxes_have_content_appended_after_containing_paragraph():
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
    result = _read_and_get_document_xml_elements(paragraph)
    assert_equal(result[1].style_id, "textbox-content")

@istest
def alternate_content_is_read_using_fallback():
    element = xml_element("mc:AlternateContent", {}, [
        xml_element("mc:Choice", {"Requires": "wps"}, [
            _paragraph_with_style_id("first")
        ]),
        xml_element("mc:Fallback", {}, [
            _paragraph_with_style_id("second")
        ])
    ])
    result = _read_and_get_document_xml_element(element)
    assert_equal("second", result.style_id)

@istest
def sdt_is_read_using_sdt_content():
    element = xml_element("w:sdt", {}, [
        xml_element("w:sdtContent", {}, [
            xml_element("w:t", {}, [xml_text("Blackdown")]),
        ]),
    ])
    result = _read_and_get_document_xml_element(element)
    assert_equal(documents.text("Blackdown"), result)

@istest
def text_nodes_are_ignored_when_reading_children():
    element = xml_element("w:r", {}, [xml_text("[text]")])
    assert_equal(
        documents.run([]),
        _read_and_get_document_xml_element(element)
    )

def _read_and_get_document_xml_element(*args, **kwargs):
    return _read_and_get_document_xml(
        lambda reader, element: reader.read_all([element]).map(single),
        *args,
        **kwargs)


def _read_and_get_document_xml_elements(*args, **kwargs):
    return _read_and_get_document_xml(
        lambda reader, element: reader.read_all([element]),
        *args,
        **kwargs)


def _read_and_get_document_xml(func, *args, **kwargs):
    styles = kwargs.pop("styles", FakeStyles())
    result = _read_document_xml(func, *args, styles=styles, **kwargs)
    assert_equal([], result.messages)
    return result.value


def _read_document_xml_element(*args, **kwargs):
    return _read_document_xml(
        lambda reader, element: reader.read_all([element]).map(single),
        *args,
        **kwargs)


def _read_document_xml_elements(*args, **kwargs):
    return _read_document_xml(
        lambda reader, element: reader.read_all([element]),
        *args,
        **kwargs)


def _read_document_xml(func, element, *args, **kwargs):
    reader = body_xml.reader(*args, **kwargs)
    return func(reader, element)


class FakeStyles(object):
    def find_paragraph_style_by_id(self, style_id):
        return Style(style_id, style_id)
    
    def find_character_style_by_id(self, style_id):
        return None
    
    def find_table_style_by_id(self, style_id):
        return None

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
    

def _create_inline_image(blip, description=None, title=None):
    return xml_element("w:drawing", {}, [
        xml_element("wp:inline", {}, _create_image_elements(blip, description=description, title=title))
    ])


def _create_anchored_image(description, blip):
    return xml_element("w:drawing", {}, [
        xml_element("wp:anchor", {}, _create_image_elements(blip, description=description, ))
    ])

    
def _create_image_elements(blip, description=None, title=None):
    properties = {}
    if description is not None:
        properties["descr"] = description
    if title is not None:
        properties["title"] = title
    
    return [
        xml_element("wp:docPr", properties),
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


def w_tr(*children):
    return xml_element("w:tr", {}, children)

def w_tc(properties=None, *children):
    return xml_element("w:tc", {}, [xml_element("w:tcPr", {}, properties)] + list(children))

def w_gridspan(val):
    return xml_element("w:gridSpan", {"w:val": val})

def w_vmerge(val):
    return xml_element("w:vMerge", {"w:val": val})


def single(values):
    if len(values) == 0:
        return None
    elif len(values) == 1:
        return values[0]
    else:
        raise Exception("Had {0} elements".format(len(values)))
