from nose.tools import istest, assert_equal

from mammoth.raw_text import extract_raw_text_from_element
from mammoth import documents


@istest
def text_element_is_converted_to_text_content():
    element = documents.Text("Hello.")

    result = extract_raw_text_from_element(element)

    assert_equal("Hello.", result)


@istest
def paragraphs_are_terminated_with_newlines():
    element = documents.paragraph(
        children=[
            documents.Text("Hello "),
            documents.Text("world."),
        ],
    )

    result = extract_raw_text_from_element(element)

    assert_equal("Hello world.\n\n", result)


@istest
def children_are_recursively_converted_to_text():
    element = documents.document([
        documents.paragraph(
            [
                documents.text("Hello "),
                documents.text("world.")
            ],
            {}
        )
    ])

    result = extract_raw_text_from_element(element)

    assert_equal("Hello world.\n\n", result)


@istest
def non_text_element_without_children_is_converted_to_empty_string():
    element = documents.line_break
    assert not hasattr(element, "children")

    result = extract_raw_text_from_element(element)

    assert_equal("", result)
