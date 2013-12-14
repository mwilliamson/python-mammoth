import io

from nose.tools import istest, assert_equal

from mammoth import documents, style_reader, results
from mammoth.conversion import convert_document_element_to_html


@istest
def plain_paragraph_is_converted_to_plain_paragraph():
    result = convert_document_element_to_html(
        documents.paragraph(children=[_run_with_text("Hello")])
    )
    assert_equal('<p>Hello</p>', result.value)


@istest
def empty_paragraphs_are_ignored():
    result = convert_document_element_to_html(
        documents.paragraph(children=[_run_with_text("")])
    )
    assert_equal('', result.value)


@istest
def paragraphs_are_converted_by_satisfying_matching_paths():
    result = convert_document_element_to_html(
        documents.paragraph(style_name="TipsParagraph", children=[
            _run_with_text("Tip")
        ]),
        styles=[
            style_reader.read_style("p.TipsParagraph => p.tip")
        ]
    )
    assert_equal('<p class="tip">Tip</p>', result.value)


@istest
def default_paragraph_style_is_used_if_no_matching_style_is_found():
    result = convert_document_element_to_html(
        documents.paragraph(style_name="TipsParagraph", children=[
            _run_with_text("Tip")
        ]),
    )
    assert_equal('<p>Tip</p>', result.value)


@istest
def default_paragraph_style_is_specified_by_mapping_plain_paragraphs():
    result = convert_document_element_to_html(
        documents.paragraph(style_name="TipsParagraph", children=[
            _run_with_text("Tip")
        ]),
        styles=[
            style_reader.read_style("p => p.tip")
        ]
    )
    assert_equal('<p class="tip">Tip</p>', result.value)
    

@istest
def warning_is_emitted_if_paragraph_style_is_unrecognised():
    result = convert_document_element_to_html(
        documents.paragraph(style_name="TipsParagraph", children=[
            _run_with_text("Tip")
        ]),
    )
    assert_equal([results.warning("Unrecognised paragraph style: TipsParagraph")], result.messages)
    

@istest
def no_warning_if_there_is_no_style_for_plain_paragraphs():
    result = convert_document_element_to_html(
        documents.paragraph(children=[_run_with_text("Tip")]),
    )
    assert_equal([], result.messages)
    

@istest
def bold_runs_are_wrapped_in_strong_tags():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_bold=True),
    )
    assert_equal("<strong>Hello</strong>", result.value)
    

@istest
def italic_runs_are_wrapped_in_emphasis_tags():
    result = convert_document_element_to_html(
        documents.run(children=[documents.text("Hello")], is_italic=True),
    )
    assert_equal("<em>Hello</em>", result.value)
    

@istest
def runs_are_converted_by_satisfying_matching_paths():
    result = convert_document_element_to_html(
        documents.run(style_name="TipsRun", children=[documents.Text("Tip")]),
        styles=[
            style_reader.read_style("r.TipsRun => span.tip")
        ]
    )
    assert_equal('<span class="tip">Tip</span>', result.value)


@istest
def docx_hyperlink_is_converted_to_anchor_tag():
    result = convert_document_element_to_html(
        documents.hyperlink(href="http://example.com", children=[documents.Text("Hello")]),
    )
    assert_equal('<a href="http://example.com">Hello</a>', result.value)


@istest
def docx_tab_is_converted_to_tab_in_html():
    result = convert_document_element_to_html(documents.tab())
    assert_equal('\t', result.value)


@istest
def images_are_converted_to_img_tags_with_data_uri():
    image = documents.image(alt_text=None, content_type="image/png", open=lambda: io.BytesIO("abc"))
    result = convert_document_element_to_html(image)
    assert_equal('<img src="data:image/png;base64,YWJj" />', result.value)


@istest
def images_have_alt_tags_if_available():
    image = documents.image(alt_text="It's a hat", content_type="image/png", open=lambda: io.BytesIO("abc"))
    result = convert_document_element_to_html(image)
    assert_equal('<img src="data:image/png;base64,YWJj" alt="It\'s a hat" />', result.value)


@istest
def can_define_custom_conversion_for_images():
    def convert_image(image, html_generator):
        with image.open() as image_file:
            html_generator.self_closing("img", {"alt": image_file.read()})
        
    image = documents.image(alt_text=None, content_type="image/png", open=lambda: io.BytesIO("abc"))
    result = convert_document_element_to_html(image, convert_image=convert_image)
    assert_equal('<img alt="abc" />', result.value)


def _run_with_text(text):
    return documents.run(children=[documents.text(text)])
