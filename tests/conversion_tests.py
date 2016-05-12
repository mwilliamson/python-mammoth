# coding=utf-8

from __future__ import unicode_literals

import io

from nose.tools import istest, assert_equal

from mammoth import documents, style_reader, results, html
from mammoth.conversion import convert_document_element_to_html
from mammoth.docx.xmlparser import parse_xml


@istest
def plain_paragraph_is_converted_to_plain_paragraph():
    result = convert_document_element_to_html(
        documents.paragraph(children=[_run_with_text("Hello")])
    )
    assert_equal('<p>Hello</p>', result.value)


@istest
def multiple_paragraphs_are_converted_to_multiple_paragraphs():
    result = convert_document_element_to_html(
        documents.document([
            documents.paragraph(children=[_run_with_text("Hello")]),
            documents.paragraph(children=[_run_with_text("there")]),
        ])
    )
    assert_equal('<p>Hello</p><p>there</p>', result.value)


@istest
def empty_paragraphs_are_ignored():
    result = convert_document_element_to_html(
        documents.paragraph(children=[_run_with_text("")])
    )
    assert_equal('', result.value)


@istest
def style_mappings_using_style_ids_can_be_used_to_map_paragraphs():
    result = convert_document_element_to_html(
        documents.paragraph(style_id="TipsParagraph", children=[
            _run_with_text("Tip")
        ]),
        style_map=[
            _style_mapping("p.TipsParagraph => p.tip")
        ]
    )
    assert_equal('<p class="tip">Tip</p>', result.value)


@istest
def style_mappings_using_style_names_can_be_used_to_map_paragraphs():
    result = convert_document_element_to_html(
        documents.paragraph(style_id="TipsParagraph", style_name="Tips Paragraph", children=[
            _run_with_text("Tip")
        ]),
        style_map=[
            _style_mapping("p[style-name='Tips Paragraph'] => p.tip")
        ]
    )
    assert_equal('<p class="tip">Tip</p>', result.value)


@istest
def style_names_in_style_mappings_are_case_insensitive():
    result = convert_document_element_to_html(
        documents.paragraph(style_id="TipsParagraph", style_name="Tips Paragraph", children=[
            _run_with_text("Tip")
        ]),
        style_map=[
            _style_mapping("p[style-name='tips paragraph'] => p.tip")
        ]
    )
    assert_equal('<p class="tip">Tip</p>', result.value)


@istest
def default_paragraph_style_is_used_if_no_matching_style_is_found():
    result = convert_document_element_to_html(
        documents.paragraph(style_id="TipsParagraph", children=[
            _run_with_text("Tip")
        ]),
    )
    assert_equal('<p>Tip</p>', result.value)


@istest
def default_paragraph_style_is_specified_by_mapping_plain_paragraphs():
    result = convert_document_element_to_html(
        documents.paragraph(style_id="TipsParagraph", children=[
            _run_with_text("Tip")
        ]),
        style_map=[
            _style_mapping("p => p.tip")
        ]
    )
    assert_equal('<p class="tip">Tip</p>', result.value)
    

@istest
def warning_is_emitted_if_paragraph_style_is_unrecognised():
    result = convert_document_element_to_html(
        documents.paragraph(
            style_id="Heading1",
            style_name="Heading 1",
            children=[_run_with_text("Tip")]
        ),
    )
    assert_equal([results.warning("Unrecognised paragraph style: Heading 1 (Style ID: Heading1)")], result.messages)
    

@istest
def no_warning_if_there_is_no_style_for_plain_paragraphs():
    result = convert_document_element_to_html(
        documents.paragraph(children=[_run_with_text("Tip")]),
    )
    assert_equal([], result.messages)


@istest
def bulleted_paragraphs_are_converted_using_matching_styles():
    result = convert_document_element_to_html(
        documents.paragraph(children=[
            _run_with_text("Hello")
        ], numbering=documents.numbering_level(level_index=0, is_ordered=False)),
        style_map=[
            _style_mapping("p:unordered-list(1) => ul > li:fresh")
        ]
    )
    assert_equal('<ul><li>Hello</li></ul>', result.value)


@istest
def bulleted_styles_dont_match_plain_paragraph():
    result = convert_document_element_to_html(
        documents.paragraph(children=[
            _run_with_text("Hello")
        ]),
        style_map=[
            _style_mapping("p:unordered-list(1) => ul > li:fresh")
        ]
    )
    assert_equal('<p>Hello</p>', result.value)
    

@istest
def bold_runs_are_wrapped_in_strong_tags_by_default():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_bold=True),
    )
    assert_equal("<strong>Hello</strong>", result.value)
    

@istest
def bold_runs_can_be_configured_with_style_mapping():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_bold=True),
        style_map=[_style_mapping("b => em")]
    )
    assert_equal("<em>Hello</em>", result.value)
    

@istest
def italic_runs_are_wrapped_in_emphasis_tags_by_default():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_italic=True),
    )
    assert_equal("<em>Hello</em>", result.value)
    

@istest
def italic_runs_can_be_configured_with_style_mapping():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_italic=True),
        style_map=[_style_mapping("i => strong")]
    )
    assert_equal("<strong>Hello</strong>", result.value)
    

@istest
def underline_runs_are_ignored_by_default():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_underline=True),
    )
    assert_equal("Hello", result.value)
    

@istest
def underline_runs_can_be_mapped_using_style_mapping():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_underline=True),
        style_map=[
            _style_mapping("u => em")
        ]
    )
    assert_equal("<em>Hello</em>", result.value)


@istest
def style_mapping_for_underline_runs_does_not_close_parent_elements():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_underline=True, is_bold=True),
        style_map=[
            _style_mapping("u => em")
        ]
    )
    assert_equal("<strong><em>Hello</em></strong>", result.value)
    

@istest
def strikethrough_runs_are_wrapped_in_s_elements_by_default():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_strikethrough=True),
    )
    assert_equal("<s>Hello</s>", result.value)


@istest
def strikethrough_runs_can_be_configured_with_style_mapping():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_strikethrough=True),
        style_map=[
            _style_mapping("strike => del")
        ]
    )
    assert_equal("<del>Hello</del>", result.value)


@istest
def superscript_runs_are_wrapped_in_sup_tags():
    result = convert_document_element_to_html(
        documents.run(
            children=[documents.text("Hello")],
            vertical_alignment=documents.VerticalAlignment.superscript,
        ),
    )
    assert_equal("<sup>Hello</sup>", result.value)
    

@istest
def subscript_runs_are_wrapped_in_sub_tags():
    result = convert_document_element_to_html(
        documents.run(
            children=[documents.text("Hello")],
            vertical_alignment=documents.VerticalAlignment.subscript,
        ),
    )
    assert_equal("<sub>Hello</sub>", result.value)
    
    
@istest
def runs_are_converted_by_satisfying_matching_paths():
    result = convert_document_element_to_html(
        documents.run(style_id="TipsRun", children=[documents.Text("Tip")]),
        style_map=[
            _style_mapping("r.TipsRun => span.tip")
        ]
    )
    assert_equal('<span class="tip">Tip</span>', result.value)


@istest
def docx_hyperlink_with_href_is_converted_to_anchor_tag():
    result = convert_document_element_to_html(
        documents.hyperlink(href="http://example.com", children=[documents.Text("Hello")]),
    )
    assert_equal('<a href="http://example.com">Hello</a>', result.value)


@istest
def docx_hyperlink_with_internal_anchor_reference_is_converted_to_anchor_tag():
    result = convert_document_element_to_html(
        documents.hyperlink(anchor="start", children=[documents.Text("Hello")]),
        id_prefix="doc-42-",
    )
    assert_equal('<a href="#doc-42-start">Hello</a>', result.value)


@istest
def bookmarks_are_converted_to_anchors_with_ids():
    result = convert_document_element_to_html(
        documents.bookmark(name="start"),
        id_prefix="doc-42-",
    )
    assert_equal('<a id="doc-42-start"></a>', result.value)


@istest
def docx_tab_is_converted_to_tab_in_html():
    result = convert_document_element_to_html(documents.tab())
    assert_equal('\t', result.value)


@istest
def docx_table_is_converted_to_table_in_html():
    table = documents.table([
        documents.table_row([
            documents.table_cell([_paragraph_with_text("Top left")]),
            documents.table_cell([_paragraph_with_text("Top right")]),
        ]),
        documents.table_row([
            documents.table_cell([_paragraph_with_text("Bottom left")]),
            documents.table_cell([_paragraph_with_text("Bottom right")]),
        ]),
    ])
    result = convert_document_element_to_html(table)
    expected_html = (
        "<table>" +
        "<tr><td><p>Top left</p></td><td><p>Top right</p></td></tr>" +
        "<tr><td><p>Bottom left</p></td><td><p>Bottom right</p></td></tr>" +
        "</table>")
    assert_equal(expected_html, result.value)


@istest
def empty_cells_are_preserved_in_table():
    table = documents.table([
        documents.table_row([
            documents.table_cell([_paragraph_with_text("")]),
            documents.table_cell([_paragraph_with_text("Top right")]),
        ]),
    ])
    result = convert_document_element_to_html(table)
    expected_html = (
        "<table>" +
        "<tr><td></td><td><p>Top right</p></td></tr>" +
        "</table>")
    assert_equal(expected_html, result.value)


@istest
def table_cells_are_written_with_colspan_if_not_equal_to_one():
    table = documents.table([
        documents.table_row([
            documents.table_cell([_paragraph_with_text("Top left")], colspan=2),
            documents.table_cell([_paragraph_with_text("Top right")]),
        ]),
    ])
    result = convert_document_element_to_html(table)
    expected_html = (
        "<table>" +
        "<tr><td colspan=\"2\"><p>Top left</p></td><td><p>Top right</p></td></tr>" +
        "</table>")
    assert_equal(expected_html, result.value)


@istest
def table_cells_are_written_with_rowspan_if_not_equal_to_one():
    table = documents.table([
        documents.table_row([
            documents.table_cell([], rowspan=2),
        ]),
    ])
    result = convert_document_element_to_html(table)
    expected_html = (
        "<table>" +
        "<tr><td rowspan=\"2\"></td></tr>" +
        "</table>")
    assert_equal(expected_html, result.value)


@istest
def line_break_is_converted_to_br():
    line_break = documents.line_break()
    result = convert_document_element_to_html(line_break)
    assert_equal("<br />", result.value)


@istest
def images_are_converted_to_img_tags_with_data_uri():
    image = documents.image(alt_text=None, content_type="image/png", open=lambda: io.BytesIO(b"abc"))
    result = convert_document_element_to_html(image)
    assert_equal('<img src="data:image/png;base64,YWJj" />', result.value)


@istest
def images_have_alt_tags_if_available():
    image = documents.image(alt_text="It's a hat", content_type="image/png", open=lambda: io.BytesIO(b"abc"))
    result = convert_document_element_to_html(image)
    image_html = parse_xml(io.StringIO(result.value))
    assert_equal('It\'s a hat', image_html.attributes["alt"])


@istest
def can_define_custom_conversion_for_images():
    def convert_image(image):
        with image.open() as image_file:
            return [html.self_closing_element("img", {"alt": image_file.read().decode("ascii")})]
        
    image = documents.image(alt_text=None, content_type="image/png", open=lambda: io.BytesIO(b"abc"))
    result = convert_document_element_to_html(image, convert_image=convert_image)
    assert_equal('<img alt="abc" />', result.value)


@istest
def footnote_reference_is_converted_to_superscript_intra_page_link():
    footnote_reference = documents.note_reference("footnote", "4")
    result = convert_document_element_to_html(
        footnote_reference,
        id_prefix="doc-42-"
    )
    assert_equal('<sup><a href="#doc-42-footnote-4" id="doc-42-footnote-ref-4">[1]</a></sup>', result.value)


@istest
def footnotes_are_included_after_the_main_body():
    footnote_reference = documents.note_reference("footnote", "4")
    document = documents.document(
        [documents.paragraph([
            _run_with_text("Knock knock"),
            documents.run([footnote_reference])
        ])],
        notes=documents.notes([
            documents.note("footnote", "4", [_paragraph_with_text("Who's there?")])
        ])
    )
    result = convert_document_element_to_html(
        document,
        id_prefix="doc-42-"
    )
    expected_html = ('<p>Knock knock<sup><a href="#doc-42-footnote-4" id="doc-42-footnote-ref-4">[1]</a></sup></p>' +
                '<ol><li id="doc-42-footnote-4"><p>Who\'s there? <a href="#doc-42-footnote-ref-4">↑</a></p></li></ol>')
    assert_equal(expected_html, result.value)


def _paragraph_with_text(text):
    return documents.paragraph(children=[_run_with_text(text)])


def _run_with_text(text):
    return documents.run(children=[documents.text(text)])


def _style_mapping(text):
    result = style_reader.read_style(text)
    assert not result.messages
    return result.value
